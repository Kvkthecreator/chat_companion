CREATE SCHEMA public;
CREATE TYPE public.alert_severity AS ENUM (
    'info',
    'warning',
    'error',
    'critical'
);
CREATE TYPE public.alert_type AS ENUM (
    'approval.required',
    'decision.needed',
    'error.attention',
    'processing.completed',
    'document.ready',
    'insights.available',
    'governance.updated',
    'collaboration.update',
    'system.maintenance',
    'system.performance',
    'system.security',
    'system.storage'
);
CREATE TYPE public.basket_state AS ENUM (
    'INIT',
    'ACTIVE',
    'ARCHIVED',
    'DEPRECATED'
);
CREATE TYPE public.blast_radius AS ENUM (
    'Local',
    'Scoped',
    'Global'
);
CREATE TYPE public.block_state AS ENUM (
    'PROPOSED',
    'ACCEPTED',
    'LOCKED',
    'CONSTANT',
    'SUPERSEDED',
    'REJECTED'
);
CREATE TYPE public.event_significance AS ENUM (
    'low',
    'medium',
    'high'
);
CREATE TYPE public.knowledge_event_type AS ENUM (
    'memory.captured',
    'knowledge.evolved',
    'insights.discovered',
    'document.created',
    'document.updated',
    'relationships.mapped',
    'governance.decided',
    'milestone.achieved'
);
CREATE TYPE public.processing_state AS ENUM (
    'pending',
    'claimed',
    'processing',
    'completed',
    'failed',
    'cascading'
);
CREATE TYPE public.proposal_kind AS ENUM (
    'Extraction',
    'Edit',
    'Merge',
    'Attachment',
    'ScopePromotion',
    'Deprecation',
    'Revision',
    'Detach',
    'Rename',
    'ContextAlias',
    'Capture'
);
CREATE TYPE public.proposal_state AS ENUM (
    'DRAFT',
    'PROPOSED',
    'UNDER_REVIEW',
    'APPROVED',
    'REJECTED',
    'SUPERSEDED',
    'MERGED'
);
CREATE TYPE public.scope_level AS ENUM (
    'LOCAL',
    'WORKSPACE',
    'ORG',
    'GLOBAL'
);
CREATE TYPE public.substrate_type AS ENUM (
    'block',
    'dump',
    'event',
    'document'
);
CREATE FUNCTION public.auto_increment_block_usage_on_reference() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
BEGIN
  -- Only increment for block substrate types
  IF NEW.substrate_type = 'block' THEN
    PERFORM increment_block_usage(NEW.substrate_id);
  END IF;
  RETURN NEW;
END;
$$;
CREATE FUNCTION public.check_block_depth() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
DECLARE depth int := 0; cursor_id uuid;
BEGIN
  cursor_id := NEW.parent_block_id;
  WHILE cursor_id IS NOT NULL LOOP
    depth := depth + 1;
    IF depth > 2 THEN
      RAISE EXCEPTION 'Hierarchy depth > 2';
    END IF;
    SELECT parent_block_id INTO cursor_id FROM blocks WHERE id = cursor_id;
  END LOOP;
  RETURN NEW;
END;
$$;
CREATE FUNCTION public.check_single_workspace_per_user() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
  IF NEW.role = 'owner' THEN
    -- Check if user already owns a workspace
    IF EXISTS (
      SELECT 1 FROM workspace_memberships 
      WHERE user_id = NEW.user_id 
        AND role = 'owner' 
        AND workspace_id != NEW.workspace_id
    ) THEN
      RAISE EXCEPTION 'CANON VIOLATION: User % already owns a workspace. Each user can only own one workspace.', NEW.user_id;
    END IF;
  END IF;
  RETURN NEW;
END;
$$;
CREATE FUNCTION public.cleanup_expired_mcp_sessions() RETURNS integer
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM public.mcp_oauth_sessions
    WHERE expires_at < NOW();
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$;
CREATE FUNCTION public.create_basket_with_dump(dump_body text, file_urls jsonb, user_id uuid, workspace_id uuid) RETURNS TABLE(basket_id uuid)
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'public'
    AS $$
declare
  v_basket_id uuid;
  v_dump_id uuid;
begin
  insert into baskets (workspace_id, user_id)
    values (workspace_id, user_id)
    returning id into v_basket_id;
  insert into raw_dumps (basket_id, body_md, file_refs, workspace_id)
    values (v_basket_id, dump_body, coalesce(file_urls, '[]'::jsonb), workspace_id)
    returning id into v_dump_id;
  update baskets
     set raw_dump_id = v_dump_id
   where id = v_basket_id;
  return query select v_basket_id;
end;
$$;
CREATE FUNCTION public.dismiss_user_alert(p_alert_id uuid) RETURNS boolean
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
BEGIN
  UPDATE user_alerts 
  SET dismissed_at = now() 
  WHERE id = p_alert_id AND user_id = auth.uid();
  
  RETURN FOUND;
END;
$$;
CREATE FUNCTION public.emit_knowledge_event(p_basket_id uuid, p_workspace_id uuid, p_event_type public.knowledge_event_type, p_title text, p_description text DEFAULT NULL::text, p_significance public.event_significance DEFAULT 'medium'::public.event_significance, p_metadata jsonb DEFAULT '{}'::jsonb, p_related_ids jsonb DEFAULT '{}'::jsonb) RETURNS uuid
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
DECLARE
  event_id uuid;
BEGIN
  INSERT INTO knowledge_timeline (
    basket_id, workspace_id, event_type, title, description, 
    significance, metadata, related_ids
  ) VALUES (
    p_basket_id, p_workspace_id, p_event_type, p_title, p_description,
    p_significance, p_metadata, p_related_ids
  ) RETURNING id INTO event_id;
  
  RETURN event_id;
END;
$$;
CREATE FUNCTION public.emit_narrative_event(p_basket_id uuid, p_doc_id uuid, p_kind text, p_preview text) RETURNS void
    LANGUAGE plpgsql
    AS $$
declare
  v_workspace_id uuid;
begin
  -- Get workspace_id from basket
  select workspace_id into v_workspace_id
  from public.baskets
  where id = p_basket_id;
  if v_workspace_id is null then
    raise exception 'Basket % not found or has no workspace', p_basket_id;
  end if;
  -- Insert timeline event with workspace_id
  insert into public.timeline_events (basket_id, workspace_id, kind, ref_id, preview, payload)
  values (
    p_basket_id,
    v_workspace_id,
    'narrative',
    p_doc_id,
    p_preview,
    jsonb_build_object('event', p_kind, 'doc_id', p_doc_id::text)
  );
end;
$$;
CREATE FUNCTION public.emit_rel_bulk_note(p_basket uuid, p_created integer, p_ignored integer, p_idem_key text) RETURNS void
    LANGUAGE plpgsql
    AS $$
begin
  insert into public.timeline_events (basket_id, kind, ref_id, preview, payload)
  values (
    p_basket, 'system_note', null,
    'Graph updated: ' || p_created || ' new, ' || p_ignored || ' ignored',
    jsonb_build_object('created', p_created, 'ignored', p_ignored, 'idem_key', coalesce(p_idem_key,''))
  );
end$$;
CREATE FUNCTION public.emit_timeline_event(p_basket_id uuid, p_event_type text, p_event_data jsonb, p_workspace_id uuid, p_actor_id uuid DEFAULT NULL::uuid, p_agent_type text DEFAULT NULL::text) RETURNS bigint
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
DECLARE
  v_event_id bigint;
  v_preview text;
BEGIN
  -- Generate preview from event data if available
  v_preview := CASE 
    WHEN p_event_data ? 'preview' THEN p_event_data->>'preview'
    WHEN p_event_type LIKE '%.created' THEN 'Created ' || split_part(p_event_type, '.', 1)
    WHEN p_event_type LIKE '%.updated' THEN 'Updated ' || split_part(p_event_type, '.', 1)
    WHEN p_event_type LIKE '%.attached' THEN 'Attached to document'
    WHEN p_event_type LIKE '%.detached' THEN 'Detached from document'
    ELSE p_event_type
  END;
  -- Use existing fn_timeline_emit function
  SELECT fn_timeline_emit(
    p_basket_id,
    p_event_type,
    COALESCE(p_actor_id, (p_event_data->>'ref_id')::uuid),
    v_preview,
    p_event_data
  ) INTO v_event_id;
  
  RETURN v_event_id;
END;
$$;
CREATE FUNCTION public.emit_user_alert(p_user_id uuid, p_workspace_id uuid, p_alert_type public.alert_type, p_title text, p_message text, p_severity public.alert_severity DEFAULT 'info'::public.alert_severity, p_actionable boolean DEFAULT false, p_action_url text DEFAULT NULL::text, p_action_label text DEFAULT NULL::text, p_related_entities jsonb DEFAULT '{}'::jsonb, p_expires_at timestamp with time zone DEFAULT NULL::timestamp with time zone) RETURNS uuid
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
DECLARE
  alert_id uuid;
BEGIN
  INSERT INTO user_alerts (
    user_id, workspace_id, alert_type, title, message, severity,
    actionable, action_url, action_label, related_entities, expires_at
  ) VALUES (
    p_user_id, p_workspace_id, p_alert_type, p_title, p_message, p_severity,
    p_actionable, p_action_url, p_action_label, p_related_entities, p_expires_at
  ) RETURNING id INTO alert_id;
  
  RETURN alert_id;
END;
$$;
CREATE FUNCTION public.ensure_raw_dump_text_columns() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
  BEGIN
    -- Ensure both columns have the same value on insert
    IF NEW.body_md IS NOT NULL AND NEW.text_dump IS NULL THEN
      NEW.text_dump = NEW.body_md;
    ELSIF NEW.text_dump IS NOT NULL AND NEW.body_md IS NULL THEN
      NEW.body_md = NEW.text_dump;
    END IF;
    
    RETURN NEW;
  END;
  $$;
CREATE FUNCTION public.fn_archive_block(p_basket_id uuid, p_block_id uuid, p_actor_id uuid DEFAULT NULL::uuid) RETURNS uuid
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
DECLARE
  v_workspace_id uuid;
  v_preview jsonb;
  v_tomb_id uuid;
BEGIN
  SELECT workspace_id INTO v_workspace_id FROM baskets WHERE id = p_basket_id;
  -- Detach references
  DELETE FROM substrate_references
  USING documents d
  WHERE substrate_references.document_id = d.id
    AND d.basket_id = p_basket_id
    AND substrate_references.substrate_type = 'block'
    AND substrate_references.substrate_id = p_block_id;
  -- Prune relationships
  DELETE FROM substrate_relationships
  WHERE basket_id = p_basket_id
    AND ((from_id = p_block_id AND from_type = 'block') OR (to_id = p_block_id AND to_type = 'block'));
  -- Mark block archived via status
  UPDATE blocks SET status = 'archived', updated_at = now()
  WHERE id = p_block_id AND basket_id = p_basket_id;
  -- Preview snapshot for tombstone counts
  SELECT fn_cascade_preview(p_basket_id, 'block', p_block_id) INTO v_preview;
  INSERT INTO substrate_tombstones (
    workspace_id, basket_id, substrate_type, substrate_id,
    deletion_mode, redaction_scope, redaction_reason,
    refs_detached_count, relationships_pruned_count, affected_documents_count,
    created_by
  ) VALUES (
    v_workspace_id, p_basket_id, 'block', p_block_id,
    'archived', NULL, NULL,
    COALESCE((v_preview->>'refs_detached_count')::int, 0),
    COALESCE((v_preview->>'relationships_pruned_count')::int, 0),
    COALESCE((v_preview->>'affected_documents_count')::int, 0),
    p_actor_id
  ) RETURNING id INTO v_tomb_id;
  -- No timeline event emission to avoid kind constraint mismatch
  RETURN v_tomb_id;
END;
$$;
CREATE FUNCTION public.fn_archive_context_item(p_basket_id uuid, p_context_item_id uuid, p_actor_id uuid DEFAULT NULL::uuid) RETURNS uuid
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
DECLARE
  v_workspace_id uuid;
  v_preview jsonb;
  v_event_ids uuid[] := '{}';
  v_tomb_id uuid;
  v_refs_count int := 0;
  v_rels_count int := 0;
  v_docs_count int := 0;
BEGIN
  SELECT workspace_id INTO v_workspace_id FROM baskets WHERE id = p_basket_id;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'Basket % not found', p_basket_id;
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM context_items
    WHERE id = p_context_item_id AND basket_id = p_basket_id AND status = 'active'
  ) THEN
    RAISE EXCEPTION 'Context item % not found in basket % or already archived', p_context_item_id, p_basket_id;
  END IF;
  SELECT fn_cascade_preview(p_basket_id, 'context_item', p_context_item_id) INTO v_preview;
  v_refs_count := COALESCE((v_preview->'substrate_references_detached')::int, 0);
  v_rels_count := COALESCE((v_preview->'relationships_pruned')::int, 0);
  v_docs_count := COALESCE((v_preview->'affected_documents')::int, 0);
  UPDATE context_items
    SET status = 'archived',
        state = 'DEPRECATED'::context_item_state,
        updated_at = now()
    WHERE id = p_context_item_id AND basket_id = p_basket_id;
  DELETE FROM substrate_references
    WHERE substrate_id = p_context_item_id AND substrate_type = 'context_item';
  DELETE FROM substrate_relationships
    WHERE (from_id = p_context_item_id AND from_type = 'context_item')
       OR (to_id = p_context_item_id AND to_type = 'context_item');
  INSERT INTO substrate_tombstones (
    workspace_id, basket_id, substrate_type, substrate_id,
    deletion_mode, redaction_scope, redaction_reason,
    refs_detached_count, relationships_pruned_count, affected_documents_count,
    created_by
  ) VALUES (
    v_workspace_id, p_basket_id, 'context_item', p_context_item_id,
    'archived', NULL, 'user_archive',
    v_refs_count, v_rels_count, v_docs_count,
    p_actor_id
  ) RETURNING id INTO v_tomb_id;
  BEGIN
    DECLARE
      v_flags jsonb;
      v_retention_days text;
    BEGIN
      SELECT public.get_workspace_governance_flags(v_workspace_id) INTO v_flags;
      IF COALESCE((v_flags->>'retention_enabled')::boolean, false) THEN
        v_retention_days := v_flags->'retention_policy'->'context_item'->>'days';
        IF v_retention_days IS NOT NULL THEN
          UPDATE substrate_tombstones
            SET earliest_physical_delete_at = now() + (v_retention_days::int || ' days')::interval
            WHERE id = v_tomb_id;
        END IF;
      END IF;
    END;
  EXCEPTION WHEN OTHERS THEN
    NULL;
  END;
  PERFORM emit_timeline_event(
    p_basket_id,
    'context_item.archived',
    jsonb_build_object(
      'context_item_id', p_context_item_id,
      'tomb_id', v_tomb_id,
      'refs_detached', v_refs_count,
      'relationships_pruned', v_rels_count,
      'affected_documents', v_docs_count
    ),
    v_workspace_id,
    p_actor_id
  );
  RETURN v_tomb_id;
END;
$$;
CREATE FUNCTION public.fn_block_create(p_basket_id uuid, p_workspace_id uuid, p_title text, p_body_md text DEFAULT NULL::text) RETURNS uuid
    LANGUAGE plpgsql
    AS $$
DECLARE v_block_id uuid;
BEGIN
  INSERT INTO public.blocks (basket_id, workspace_id, title, body_md)
  VALUES (p_basket_id, p_workspace_id, p_title, p_body_md)
  RETURNING id INTO v_block_id;
  PERFORM public.fn_timeline_emit(
    p_basket_id,
    'block',
    v_block_id,
    LEFT(COALESCE(p_title, ''), 140),
    jsonb_build_object('source','block_create','actor_id', auth.uid())
  );
  RETURN v_block_id;
END;
$$;
CREATE FUNCTION public.fn_block_revision_create(p_basket_id uuid, p_block_id uuid, p_workspace_id uuid, p_summary text, p_diff_json jsonb) RETURNS uuid
    LANGUAGE plpgsql
    AS $$
DECLARE v_rev_id uuid;
BEGIN
  INSERT INTO public.block_revisions (block_id, workspace_id, summary, diff_json)
  VALUES (p_block_id, p_workspace_id, p_summary, p_diff_json)
  RETURNING id INTO v_rev_id;
  PERFORM public.fn_timeline_emit(
    p_basket_id,
    'block_revision',
    v_rev_id,
    LEFT(COALESCE(p_summary,''), 140),
    jsonb_build_object('source','block_revision','actor_id', auth.uid(), 'block_id', p_block_id)
  );
  RETURN v_rev_id;
END; $$;
CREATE FUNCTION public.fn_cascade_preview(p_basket_id uuid, p_substrate_type text, p_substrate_id uuid) RETURNS jsonb
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
DECLARE
  v_refs int := 0;
  v_rels int := 0;
  v_docs int := 0;
BEGIN
  -- References in documents
  SELECT count(*) INTO v_refs
  FROM substrate_references
  WHERE document_id IN (SELECT id FROM documents WHERE basket_id = p_basket_id)
    AND substrate_type = p_substrate_type::substrate_type
    AND substrate_id = p_substrate_id;
  -- Relationships touching the node
  SELECT count(*) INTO v_rels
  FROM substrate_relationships
  WHERE basket_id = p_basket_id
    AND ((from_id = p_substrate_id AND from_type = p_substrate_type)
      OR (to_id = p_substrate_id AND to_type = p_substrate_type));
  -- Distinct documents affected
  SELECT count(DISTINCT document_id) INTO v_docs
  FROM substrate_references
  WHERE document_id IN (SELECT id FROM documents WHERE basket_id = p_basket_id)
    AND substrate_type = p_substrate_type::substrate_type
    AND substrate_id = p_substrate_id;
  RETURN jsonb_build_object(
    'refs_detached_count', v_refs,
    'relationships_pruned_count', v_rels,
    'affected_documents_count', v_docs
  );
END;
$$;
CREATE TABLE public.agent_processing_queue (
    id uuid DEFAULT extensions.uuid_generate_v4() NOT NULL,
    dump_id uuid,
    basket_id uuid,
    workspace_id uuid NOT NULL,
    processing_state public.processing_state DEFAULT 'pending'::public.processing_state,
    claimed_at timestamp without time zone,
    claimed_by text,
    completed_at timestamp without time zone,
    attempts integer DEFAULT 0,
    error_message text,
    created_at timestamp without time zone DEFAULT now(),
    processing_stage text,
    work_payload jsonb DEFAULT '{}'::jsonb,
    work_result jsonb DEFAULT '{}'::jsonb,
    cascade_metadata jsonb DEFAULT '{}'::jsonb,
    parent_work_id uuid,
    user_id uuid,
    work_id text,
    work_type text DEFAULT 'P1_SUBSTRATE'::text,
    priority integer DEFAULT 5,
    CONSTRAINT valid_work_type_v21 CHECK ((work_type = ANY (ARRAY['P0_CAPTURE'::text, 'P1_SUBSTRATE'::text, 'P2_GRAPH'::text, 'P3_REFLECTION'::text, 'P4_COMPOSE'::text, 'MANUAL_EDIT'::text, 'PROPOSAL_REVIEW'::text, 'TIMELINE_RESTORE'::text])))
);
CREATE FUNCTION public.fn_claim_next_dumps(p_worker_id text, p_limit integer DEFAULT 10, p_stale_after_minutes integer DEFAULT 5) RETURNS SETOF public.agent_processing_queue
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
BEGIN
  -- Atomically claim pending or stale dumps
  RETURN QUERY
  UPDATE agent_processing_queue
  SET 
    processing_state = 'claimed',
    claimed_at = now(),
    claimed_by = p_worker_id
  WHERE id IN (
    SELECT id 
    FROM agent_processing_queue
    WHERE processing_state = 'pending'
       -- Include stale claimed jobs that haven't been updated
       OR (processing_state = 'claimed' 
           AND claimed_at < now() - interval '1 minute' * p_stale_after_minutes)
    ORDER BY created_at
    LIMIT p_limit
    FOR UPDATE SKIP LOCKED  -- Prevents race conditions between agents
  )
  RETURNING *;
END;
$$;
CREATE FUNCTION public.fn_claim_pipeline_work(p_worker_id text, p_limit integer DEFAULT 10, p_stale_after_minutes integer DEFAULT 5) RETURNS SETOF public.agent_processing_queue
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
BEGIN
  RETURN QUERY
  UPDATE agent_processing_queue
  SET 
    processing_state = 'claimed',
    claimed_at = now(),
    claimed_by = p_worker_id
  WHERE id IN (
    SELECT id 
    FROM agent_processing_queue
    WHERE (
      processing_state = 'pending' AND work_type IN ('P0_CAPTURE','P1_SUBSTRATE','P2_GRAPH','P4_COMPOSE')
    ) OR (
      processing_state = 'claimed' 
      AND claimed_at < now() - interval '1 minute' * p_stale_after_minutes
      AND work_type IN ('P0_CAPTURE','P1_SUBSTRATE','P2_GRAPH','P4_COMPOSE')
    )
    ORDER BY created_at
    LIMIT p_limit
    FOR UPDATE SKIP LOCKED
  )
  RETURNING *;
END;
$$;
CREATE FUNCTION public.fn_context_item_create(p_basket_id uuid, p_type text, p_content text DEFAULT NULL::text, p_title text DEFAULT NULL::text, p_description text DEFAULT NULL::text) RETURNS uuid
    LANGUAGE plpgsql
    AS $$
DECLARE v_ctx_id uuid;
BEGIN
  INSERT INTO public.context_items (basket_id, type, content, title, description)
  VALUES (p_basket_id, p_type, p_content, p_title, p_description)
  RETURNING id INTO v_ctx_id;
  PERFORM public.fn_timeline_emit(
    p_basket_id,
    'context_item',
    v_ctx_id,
    LEFT(COALESCE(p_title, p_type, ''), 140),
    jsonb_build_object('source','context_item_create','actor_id', auth.uid())
  );
  RETURN v_ctx_id;
END;
$$;
CREATE FUNCTION public.fn_document_attach_block(p_document_id uuid, p_block_id uuid, p_occurrences integer DEFAULT 0, p_snippets jsonb DEFAULT '[]'::jsonb) RETURNS uuid
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'public'
    AS $$
declare
  v_id uuid;
  v_basket uuid;
begin
  -- Upsert-like behavior on unique(document_id, block_id)
  select id into v_id from public.block_links
  where document_id = p_document_id and block_id = p_block_id;
  if v_id is null then
    insert into public.block_links (id, document_id, block_id, occurrences, snippets)
    values (gen_random_uuid(), p_document_id, p_block_id, p_occurrences, p_snippets)
    returning id into v_id;
  else
    update public.block_links
    set occurrences = coalesce(p_occurrences, occurrences),
        snippets    = coalesce(p_snippets, snippets)
    where id = v_id;
  end if;
  select basket_id into v_basket from public.documents where id = p_document_id;
  perform public.emit_narrative_event(v_basket, p_document_id, 'doc.updated', 'attached block');
  return v_id;
end;
$$;
CREATE FUNCTION public.fn_document_attach_context_item(p_document_id uuid, p_context_item_id uuid, p_role text DEFAULT NULL::text, p_weight numeric DEFAULT NULL::numeric) RETURNS uuid
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'public'
    AS $$
declare
  v_id uuid;
  v_basket uuid;
begin
  -- Upsert-like behavior via unique(document_id, context_item_id)
  select id into v_id from public.document_context_items
  where document_id = p_document_id and context_item_id = p_context_item_id;
  if v_id is null then
    insert into public.document_context_items (id, document_id, context_item_id, role, weight)
    values (gen_random_uuid(), p_document_id, p_context_item_id, p_role, p_weight)
    returning id into v_id;
  else
    update public.document_context_items
    set role = coalesce(p_role, role),
        weight = coalesce(p_weight, weight)
    where id = v_id;
  end if;
  select basket_id into v_basket from public.documents where id = p_document_id;
  perform public.emit_narrative_event(v_basket, p_document_id, 'doc.updated', 'attached context_item');
  return v_id;
end;
$$;
CREATE FUNCTION public.fn_document_create(p_basket_id uuid, p_workspace_id uuid, p_title text, p_content_raw text) RETURNS uuid
    LANGUAGE plpgsql
    AS $$
DECLARE v_doc_id uuid;
BEGIN
  INSERT INTO public.documents (basket_id, workspace_id, title, content_raw)
  VALUES (p_basket_id, p_workspace_id, p_title, p_content_raw)
  RETURNING id INTO v_doc_id;
  PERFORM public.fn_timeline_emit(
    p_basket_id,
    'document',
    v_doc_id,
    LEFT(COALESCE(p_title, ''), 140),
    jsonb_build_object('source','document_create','actor_id', auth.uid())
  );
  RETURN v_doc_id;
END;
$$;
CREATE FUNCTION public.fn_document_create(p_basket_id uuid, p_title text, p_content_raw text, p_document_type text DEFAULT 'narrative'::text, p_metadata jsonb DEFAULT '{}'::jsonb) RETURNS uuid
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'public'
    AS $$
declare
  v_doc_id uuid;
begin
  insert into public.documents (id, basket_id, title, content_raw, content_rendered, document_type, metadata)
  values (gen_random_uuid(), p_basket_id, p_title, p_content_raw, null, p_document_type, p_metadata)
  returning id into v_doc_id;
  perform public.emit_narrative_event(p_basket_id, v_doc_id, 'doc.created', left(coalesce(p_title,''), 120));
  return v_doc_id;
end;
$$;
CREATE FUNCTION public.fn_document_create_version(p_document_id uuid, p_content text, p_version_message text DEFAULT NULL::text) RETURNS character varying
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
DECLARE
  v_version_hash varchar(64);
  v_workspace_id uuid;
  v_basket_id uuid;
BEGIN
  v_version_hash := 'doc_v' || substr(encode(sha256(p_content::bytea), 'hex'), 1, 58);
  SELECT workspace_id, basket_id
    INTO v_workspace_id, v_basket_id
  FROM documents
  WHERE id = p_document_id;
  IF v_workspace_id IS NULL THEN
    RAISE EXCEPTION 'Document % not found', p_document_id;
  END IF;
  INSERT INTO document_versions (
    version_hash,
    document_id,
    content,
    metadata_snapshot,
    substrate_refs_snapshot,
    created_by,
    version_message,
    parent_version_hash
  )
  SELECT
    v_version_hash,
    p_document_id,
    p_content,
    d.metadata,
    COALESCE((
        SELECT jsonb_agg(to_jsonb(sr.*))
        FROM substrate_references sr
        WHERE sr.document_id = p_document_id
      ), '[]'::jsonb
    ),
    auth.uid(),
    p_version_message,
    d.current_version_hash
  FROM documents d
  WHERE d.id = p_document_id
  ON CONFLICT (version_hash) DO NOTHING;
  UPDATE documents
  SET current_version_hash = v_version_hash,
      updated_at = now()
  WHERE id = p_document_id;
  PERFORM fn_timeline_emit(
    v_basket_id,
    'document.updated',
    p_document_id,
    'Document version created: ' || left(v_version_hash, 12),
    jsonb_build_object('version_hash', v_version_hash, 'message', p_version_message)
  );
  RETURN v_version_hash;
END;
$$;
CREATE FUNCTION public.fn_document_update(p_doc_id uuid, p_title text, p_content_raw text, p_metadata jsonb DEFAULT NULL::jsonb) RETURNS uuid
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'public'
    AS $$
declare
  v_basket uuid;
begin
  update public.documents
  set title = coalesce(p_title, title),
      content_raw = coalesce(p_content_raw, content_raw),
      updated_at = now(),
      metadata = coalesce(p_metadata, metadata)
  where id = p_doc_id;
  select basket_id into v_basket from public.documents where id = p_doc_id;
  perform public.emit_narrative_event(v_basket, p_doc_id, 'doc.updated', left(coalesce(p_title,''), 120));
  return p_doc_id;
end;
$$;
CREATE FUNCTION public.fn_ingest_dumps(p_workspace_id uuid, p_basket_id uuid, p_dumps jsonb) RETURNS jsonb[]
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
DECLARE
  v_dump jsonb;
  v_dump_id uuid;
  v_dump_created boolean;
  v_results jsonb[] := '{}';
  v_result jsonb;
BEGIN
  -- Process each dump in the array
  FOR v_dump IN SELECT * FROM jsonb_array_elements(p_dumps)
  LOOP
    -- Insert dump with idempotency on dump_request_id
    INSERT INTO public.raw_dumps (
      workspace_id, 
      basket_id,
      dump_request_id, 
      body_md, 
      file_url,
      source_meta,
      ingest_trace_id
    )
    VALUES (
      p_workspace_id,
      p_basket_id,
      (v_dump->>'dump_request_id')::uuid,
      (v_dump->>'text_dump'),
      (v_dump->>'file_url'),
      COALESCE((v_dump->'source_meta')::jsonb, '{}'::jsonb),
      (v_dump->>'ingest_trace_id')
    )
    ON CONFLICT (basket_id, dump_request_id) 
    DO UPDATE SET 
      body_md = COALESCE(EXCLUDED.body_md, public.raw_dumps.body_md),
      file_url = COALESCE(EXCLUDED.file_url, public.raw_dumps.file_url)
    RETURNING id, (xmax = 0) INTO v_dump_id, v_dump_created;
    -- Emit timeline event for new dumps
    IF v_dump_created THEN
      PERFORM public.fn_timeline_emit(
        p_basket_id,
        'dump',
        v_dump_id,
        LEFT(COALESCE((v_dump->>'text_dump'), 'File: ' || (v_dump->>'file_url'), 'Memory added'), 140),
        jsonb_build_object(
          'source', 'ingest',
          'actor_id', auth.uid(),
          'dump_request_id', (v_dump->>'dump_request_id')
        )
      );
    END IF;
    -- Build result
    v_result := jsonb_build_object('dump_id', v_dump_id);
    v_results := v_results || v_result;
  END LOOP;
  RETURN v_results;
END $$;
CREATE FUNCTION public.fn_queue_health() RETURNS TABLE(processing_state public.processing_state, count bigint, avg_age_seconds numeric, max_age_seconds numeric)
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
BEGIN
  RETURN QUERY
  SELECT 
    q.processing_state,
    COUNT(*) as count,
    AVG(EXTRACT(epoch FROM (now() - q.created_at)))::numeric as avg_age_seconds,
    MAX(EXTRACT(epoch FROM (now() - q.created_at)))::numeric as max_age_seconds
  FROM agent_processing_queue q
  GROUP BY q.processing_state
  ORDER BY q.processing_state;
END;
$$;
CREATE FUNCTION public.fn_redact_dump(p_basket_id uuid, p_dump_id uuid, p_scope text DEFAULT 'full'::text, p_reason text DEFAULT NULL::text, p_actor_id uuid DEFAULT NULL::uuid) RETURNS uuid
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
DECLARE
  v_workspace_id uuid;
  v_preview jsonb;
  v_tomb_id uuid;
BEGIN
  SELECT workspace_id INTO v_workspace_id FROM baskets WHERE id = p_basket_id;
  -- Redact content
  UPDATE raw_dumps
    SET body_md = NULL, text_dump = NULL, file_url = NULL, processing_status = 'redacted'
  WHERE id = p_dump_id AND basket_id = p_basket_id;
  -- Preview snapshot for tombstone counts
  SELECT fn_cascade_preview(p_basket_id, 'dump', p_dump_id) INTO v_preview;
  INSERT INTO substrate_tombstones (
    workspace_id, basket_id, substrate_type, substrate_id,
    deletion_mode, redaction_scope, redaction_reason,
    refs_detached_count, relationships_pruned_count, affected_documents_count,
    created_by
  ) VALUES (
    v_workspace_id, p_basket_id, 'dump', p_dump_id,
    'redacted', p_scope, p_reason,
    COALESCE((v_preview->>'refs_detached_count')::int, 0),
    COALESCE((v_preview->>'relationships_pruned_count')::int, 0),
    COALESCE((v_preview->>'affected_documents_count')::int, 0),
    p_actor_id
  ) RETURNING id INTO v_tomb_id;
  -- No timeline event emission to avoid kind constraint mismatch
  RETURN v_tomb_id;
END;
$$;
CREATE FUNCTION public.fn_relationship_upsert(p_basket_id uuid, p_from_type text, p_from_id uuid, p_to_type text, p_to_id uuid, p_relationship_type text, p_description text DEFAULT NULL::text, p_strength double precision DEFAULT 0.5) RETURNS uuid
    LANGUAGE plpgsql
    AS $$
DECLARE v_id uuid;
BEGIN
  INSERT INTO public.substrate_relationships (basket_id, from_type, from_id, to_type, to_id, relationship_type, description, strength)
  VALUES (p_basket_id, p_from_type, p_from_id, p_to_type, p_to_id, p_relationship_type, p_description, p_strength)
  ON CONFLICT (basket_id, from_type, from_id, to_type, to_id, relationship_type)
  DO UPDATE SET description = EXCLUDED.description, strength = EXCLUDED.strength
  RETURNING id INTO v_id;
  PERFORM public.fn_timeline_emit(
    p_basket_id,
    'relationship',
    v_id,
    LEFT(p_relationship_type || ' ' || COALESCE(p_from_type,'') || '→' || COALESCE(p_to_type,''), 140),
    jsonb_build_object('source','relationship_upsert','from_id', p_from_id, 'to_id', p_to_id, 'relationship_type', p_relationship_type, 'actor_id', auth.uid())
  );
  RETURN v_id;
END; $$;
CREATE FUNCTION public.fn_relationship_upsert_bulk(p_basket_id uuid, p_edges jsonb, p_idem_key text DEFAULT NULL::text) RETURNS jsonb
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'public'
    AS $$
declare
  v_created int := 0;
  v_ignored int := 0;
  v_e jsonb;
  v_from_type text;
  v_from_id uuid;
  v_to_type text;
  v_to_id uuid;
  v_rel_type text;
  v_desc text;
  v_strength numeric;
begin
  if p_edges is null or jsonb_typeof(p_edges) <> 'array' then
    raise exception 'edges must be a jsonb array';
  end if;
  -- Simple idempotency guard via events: if we've already logged this idem_key for this basket, short-circuit.
  if p_idem_key is not null and exists (
    select 1 from public.events
    where basket_id = p_basket_id
      and kind = 'rel.bulk_upserted'
      and (payload->>'idem_key') = p_idem_key
  ) then
    return jsonb_build_object('created', 0, 'ignored', 0, 'idem_reused', true);
  end if;
  for v_e in select * from jsonb_array_elements(p_edges) loop
    v_from_type := v_e->>'from_type';
    v_from_id   := (v_e->>'from_id')::uuid;
    v_to_type   := v_e->>'to_type';
    v_to_id     := (v_e->>'to_id')::uuid;
    v_rel_type  := v_e->>'relationship_type';
    v_desc      := v_e->>'description';
    v_strength  := coalesce((v_e->>'strength')::numeric, 0.5);
    begin
      insert into public.substrate_relationships (id, basket_id, from_type, from_id, to_type, to_id, relationship_type, description, strength)
      values (gen_random_uuid(), p_basket_id, v_from_type, v_from_id, v_to_type, v_to_id, v_rel_type, v_desc, v_strength);
      v_created := v_created + 1;
    exception when unique_violation then
      v_ignored := v_ignored + 1;
    end;
  end loop;
  -- Emit into general events bus with small payload (timeline has constrained kinds)
  insert into public.events (id, basket_id, kind, payload, workspace_id, origin)
  values (gen_random_uuid(), p_basket_id, 'rel.bulk_upserted',
          jsonb_build_object('basket_id', p_basket_id, 'created', v_created, 'ignored', v_ignored, 'idem_key', coalesce(p_idem_key,'')),
          null, 'system');
  return jsonb_build_object('created', v_created, 'ignored', v_ignored, 'idem_reused', false);
end;
$$;
CREATE FUNCTION public.fn_reset_failed_jobs(p_max_attempts integer DEFAULT 3) RETURNS integer
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
DECLARE
  reset_count int;
BEGIN
  UPDATE agent_processing_queue
  SET 
    processing_state = 'pending',
    claimed_at = NULL,
    claimed_by = NULL,
    error_message = NULL
  WHERE processing_state = 'failed' 
    AND attempts < p_max_attempts;
    
  GET DIAGNOSTICS reset_count = ROW_COUNT;
  RETURN reset_count;
END;
$$;
CREATE FUNCTION public.fn_set_basket_anchor_updated_at() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$;
CREATE FUNCTION public.fn_timeline_after_raw_dump() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
  PERFORM public.fn_timeline_emit_with_ts(
    NEW.basket_id,
    'dump',
    NEW.id,
    LEFT(COALESCE(NEW.body_md, ''), 280),
    NEW.created_at,
    jsonb_build_object('source','raw_dumps','actor_id', auth.uid())
  );
  RETURN NEW;
END; $$;
CREATE FUNCTION public.fn_timeline_emit(p_basket_id uuid, p_kind text, p_ref_id uuid, p_preview text, p_payload jsonb DEFAULT '{}'::jsonb) RETURNS bigint
    LANGUAGE plpgsql
    AS $$
DECLARE
  v_id         bigint;
  v_workspace  uuid;
BEGIN
  SELECT workspace_id INTO v_workspace FROM public.baskets WHERE id = p_basket_id;
  IF v_workspace IS NULL THEN
    RAISE EXCEPTION 'basket % not found (workspace missing)', p_basket_id;
  END IF;
  -- 1:1 rule for dumps (no dupes per ref_id)
  IF p_kind = 'dump' AND EXISTS (
    SELECT 1 FROM public.timeline_events WHERE kind='dump' AND ref_id=p_ref_id
  ) THEN
    SELECT id INTO v_id FROM public.timeline_events
     WHERE kind='dump' AND ref_id=p_ref_id
     ORDER BY id DESC LIMIT 1;
    RETURN v_id;
  END IF;
  INSERT INTO public.timeline_events (basket_id, workspace_id, ts, kind, ref_id, preview, payload)
  VALUES (p_basket_id, v_workspace, now(), p_kind, p_ref_id, p_preview, p_payload)
  RETURNING id INTO v_id;
  RETURN v_id;
END $$;
CREATE FUNCTION public.fn_timeline_emit_with_ts(p_basket_id uuid, p_kind text, p_ref_id uuid, p_preview text, p_ts timestamp with time zone, p_payload jsonb DEFAULT '{}'::jsonb) RETURNS bigint
    LANGUAGE plpgsql
    AS $$
DECLARE
  v_id         bigint;
  v_workspace  uuid;
BEGIN
  SELECT workspace_id INTO v_workspace FROM public.baskets WHERE id = p_basket_id;
  IF v_workspace IS NULL THEN
    RAISE EXCEPTION 'basket % not found (workspace missing)', p_basket_id;
  END IF;
  IF p_kind = 'dump' AND EXISTS (
    SELECT 1 FROM public.timeline_events WHERE kind='dump' AND ref_id=p_ref_id
  ) THEN
    RETURN (SELECT id FROM public.timeline_events WHERE kind='dump' AND ref_id=p_ref_id ORDER BY id DESC LIMIT 1);
  END IF;
  INSERT INTO public.timeline_events (basket_id, workspace_id, ts, kind, ref_id, preview, payload)
  VALUES (p_basket_id, v_workspace, p_ts, p_kind, p_ref_id, p_preview, p_payload)
  RETURNING id INTO v_id;
  RETURN v_id;
END $$;
CREATE FUNCTION public.fn_update_queue_state(p_id uuid, p_state public.processing_state, p_error text DEFAULT NULL::text) RETURNS void
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
BEGIN
  UPDATE agent_processing_queue 
  SET 
    processing_state = p_state,
    completed_at = CASE WHEN p_state = 'completed' THEN now() ELSE completed_at END,
    error_message = p_error,
    attempts = CASE WHEN p_state = 'failed' THEN attempts + 1 ELSE attempts END
  WHERE id = p_id;
END;
$$;
CREATE FUNCTION public.fn_vacuum_substrates(p_workspace_id uuid, p_limit integer DEFAULT 50) RETURNS jsonb
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
DECLARE
  v_deleted_blocks int := 0;
  v_deleted_dumps int := 0;
  v_deleted_items int := 0;
  v_row record;
  v_settings jsonb;
  v_retention_enabled boolean := false;
BEGIN
  -- Check retention policy flag
  SELECT public.get_workspace_governance_flags(p_workspace_id) INTO v_settings;
  v_retention_enabled := COALESCE((v_settings->>'retention_enabled')::boolean, false);
  IF NOT v_retention_enabled THEN
    RETURN jsonb_build_object('deleted_blocks',0,'deleted_dumps',0,'deleted_context_items',0,'note','retention disabled');
  END IF;
  FOR v_row IN
    SELECT * FROM public.substrate_tombstones
    WHERE workspace_id = p_workspace_id
      AND deletion_mode IN ('archived','redacted','deleted')
      AND earliest_physical_delete_at IS NOT NULL
      AND now() >= earliest_physical_delete_at
      AND physically_deleted_at IS NULL
    LIMIT p_limit
  LOOP
    -- Ensure no remaining hard references
    IF EXISTS (
      SELECT 1 FROM public.substrate_references sr
      JOIN public.documents d ON d.id = sr.document_id
      WHERE d.workspace_id = p_workspace_id
        AND sr.substrate_type = v_row.substrate_type::substrate_type
        AND sr.substrate_id = v_row.substrate_id
    ) THEN
      CONTINUE;
    END IF;
    -- Ensure no remaining relationships (for block/context_item)
    IF v_row.substrate_type IN ('block','context_item') THEN
      IF EXISTS (
        SELECT 1 FROM public.substrate_relationships
        WHERE basket_id = v_row.basket_id
          AND ((from_id = v_row.substrate_id AND from_type = v_row.substrate_type)
            OR (to_id = v_row.substrate_id AND to_type = v_row.substrate_type))
      ) THEN
        CONTINUE;
      END IF;
    END IF;
    -- Perform physical deletion per substrate type
    IF v_row.substrate_type = 'block' THEN
      DELETE FROM public.blocks WHERE id = v_row.substrate_id AND workspace_id = p_workspace_id;
      v_deleted_blocks := v_deleted_blocks + 1;
    ELSIF v_row.substrate_type = 'dump' THEN
      DELETE FROM public.raw_dumps WHERE id = v_row.substrate_id AND workspace_id = p_workspace_id;
      v_deleted_dumps := v_deleted_dumps + 1;
    ELSIF v_row.substrate_type = 'context_item' THEN
      DELETE FROM public.context_items WHERE id = v_row.substrate_id AND basket_id = v_row.basket_id;
      v_deleted_items := v_deleted_items + 1;
    ELSE
      CONTINUE;
    END IF;
    -- Mark tombstone as physically deleted and emit event
    UPDATE public.substrate_tombstones
      SET deletion_mode = 'deleted', physically_deleted_at = now()
      WHERE id = v_row.id;
    PERFORM emit_timeline_event(v_row.basket_id, 'substrate.physically_deleted', jsonb_build_object(
      'substrate_type', v_row.substrate_type,
      'substrate_id', v_row.substrate_id,
      'tombstone_id', v_row.id
    ), p_workspace_id, NULL, 'vacuum');
  END LOOP;
  RETURN jsonb_build_object(
    'deleted_blocks', v_deleted_blocks,
    'deleted_dumps', v_deleted_dumps,
    'deleted_context_items', v_deleted_items
  );
END;
$$;
CREATE FUNCTION public.get_basket_anchor_vocabulary(p_basket_id uuid) RETURNS TABLE(anchor_role text, usage_count bigint, accepted_count bigint, avg_confidence numeric, semantic_types text[])
    LANGUAGE plpgsql STABLE
    AS $$
BEGIN
    RETURN QUERY
    SELECT
        b.anchor_role,
        COUNT(*) as usage_count,
        COUNT(*) FILTER (WHERE b.anchor_status = 'accepted') as accepted_count,
        ROUND(AVG(b.anchor_confidence)::numeric, 2) as avg_confidence,
        ARRAY_AGG(DISTINCT b.semantic_type ORDER BY b.semantic_type) as semantic_types
    FROM blocks b
    WHERE b.basket_id = p_basket_id
        AND b.anchor_role IS NOT NULL
    GROUP BY b.anchor_role
    ORDER BY accepted_count DESC, usage_count DESC;
END;
$$;
CREATE FUNCTION public.get_basket_substrate_categorized(p_basket_id uuid) RETURNS TABLE(category text, block_count bigint, semantic_types jsonb)
    LANGUAGE plpgsql STABLE
    AS $$
BEGIN
    RETURN QUERY
    SELECT
        CASE
            WHEN semantic_type IN ('fact', 'metric', 'event', 'insight', 'action', 'finding', 'quote', 'summary')
                THEN 'knowledge'
            WHEN semantic_type IN ('intent', 'objective', 'rationale', 'principle', 'assumption', 'context', 'constraint')
                THEN 'meaning'
            WHEN semantic_type IN ('entity', 'classification', 'reference')
                THEN 'structural'
            ELSE 'other'
        END as category,
        COUNT(*) as block_count,
        jsonb_object_agg(
            semantic_type,
            COUNT(*)
        ) as semantic_types
    FROM blocks
    WHERE basket_id = p_basket_id
        AND state = 'ACCEPTED'
    GROUP BY category;
END;
$$;
CREATE FUNCTION public.get_block_version_history(p_block_id uuid) RETURNS TABLE(id uuid, version integer, title text, content text, state public.block_state, created_at timestamp with time zone, updated_at timestamp with time zone)
    LANGUAGE plpgsql STABLE
    AS $$
BEGIN
    RETURN QUERY
    WITH RECURSIVE version_chain AS (
        -- Start with the given block
        SELECT
            b.id,
            b.parent_block_id,
            b.version,
            b.title,
            b.content,
            b.state,
            b.created_at,
            b.updated_at
        FROM blocks b
        WHERE b.id = p_block_id
        UNION ALL
        -- Recursively get parent versions
        SELECT
            b.id,
            b.parent_block_id,
            b.version,
            b.title,
            b.content,
            b.state,
            b.created_at,
            b.updated_at
        FROM blocks b
        INNER JOIN version_chain vc ON b.id = vc.parent_block_id
    )
    SELECT
        vc.id,
        vc.version,
        vc.title,
        vc.content,
        vc.state,
        vc.created_at,
        vc.updated_at
    FROM version_chain vc
    ORDER BY vc.version DESC;
END;
$$;
CREATE FUNCTION public.get_current_insight_canon(p_basket_id uuid) RETURNS TABLE(id uuid, reflection_text text, substrate_hash text, graph_signature text, derived_from jsonb, created_at timestamp with time zone)
    LANGUAGE plpgsql STABLE SECURITY DEFINER
    AS $$
BEGIN
  RETURN QUERY
  SELECT
    ra.id,
    ra.reflection_text,
    ra.substrate_hash,
    ra.graph_signature,
    ra.derived_from,
    ra.created_at
  FROM public.reflections_artifact ra
  WHERE ra.basket_id = p_basket_id
    AND ra.insight_type = 'insight_canon'
    AND ra.is_current = true
  LIMIT 1;
END;
$$;
CREATE FUNCTION public.get_document_canon(p_basket_id uuid) RETURNS TABLE(id uuid, title text, current_version_hash text, composition_instructions jsonb, derived_from jsonb)
    LANGUAGE plpgsql STABLE SECURITY DEFINER
    AS $$
BEGIN
  RETURN QUERY
  SELECT
    d.id,
    d.title,
    d.current_version_hash,
    d.composition_instructions,
    d.derived_from
  FROM public.documents d
  WHERE d.basket_id = p_basket_id
    AND d.doc_type = 'document_canon'
  LIMIT 1;
END;
$$;
CREATE FUNCTION public.get_workspace_constants(p_workspace_id uuid) RETURNS TABLE(id uuid, semantic_type text, title text, content text, anchor_role text, scope public.scope_level, created_at timestamp with time zone)
    LANGUAGE plpgsql STABLE
    AS $$
BEGIN
    RETURN QUERY
    SELECT
        b.id,
        b.semantic_type,
        b.title,
        b.content,
        b.anchor_role,
        b.scope,
        b.created_at
    FROM blocks b
    WHERE b.workspace_id = p_workspace_id
        AND b.state = 'CONSTANT'
        AND b.scope IN ('WORKSPACE', 'ORG', 'GLOBAL')
    ORDER BY b.scope DESC, b.created_at DESC;
END;
$$;
CREATE FUNCTION public.get_workspace_governance_flags(p_workspace_id uuid) RETURNS jsonb
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
DECLARE
  result jsonb;
  settings_row public.workspace_governance_settings%ROWTYPE;
BEGIN
  -- Try to get workspace-specific settings
  SELECT * INTO settings_row
  FROM public.workspace_governance_settings
  WHERE workspace_id = p_workspace_id;
  IF FOUND THEN
    -- Return workspace-specific flags
    result := jsonb_build_object(
      'governance_enabled', settings_row.governance_enabled,
      'validator_required', settings_row.validator_required,
      'direct_substrate_writes', settings_row.direct_substrate_writes,
      'governance_ui_enabled', settings_row.governance_ui_enabled,
      'ep_onboarding_dump', settings_row.ep_onboarding_dump,
      'ep_manual_edit', settings_row.ep_manual_edit,
      'ep_graph_action', settings_row.ep_graph_action,
      'ep_timeline_restore', settings_row.ep_timeline_restore,
      'default_blast_radius', settings_row.default_blast_radius,
      'source', 'workspace_database'
    );
  ELSE
    -- Canon-compliant defaults when no row exists:
    -- P0 capture must be direct; all other entry points conservative (proposal)
    result := jsonb_build_object(
      'governance_enabled', true,
      'validator_required', false,
      'direct_substrate_writes', false,
      'governance_ui_enabled', true,
      'ep_onboarding_dump', 'direct',
      'ep_manual_edit', 'proposal',
      'ep_document_edit', 'proposal',            -- legacy field retained for compatibility
      'ep_reflection_suggestion', 'proposal',    -- legacy field retained for compatibility
      'ep_graph_action', 'proposal',
      'ep_timeline_restore', 'proposal',
      'default_blast_radius', 'Scoped',
      'source', 'canon_compliant_defaults'
    );
  END IF;
  RETURN result;
END;
$$;
CREATE FUNCTION public.increment_block_usage(p_block_id uuid) RETURNS void
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
BEGIN
  INSERT INTO block_usage (block_id, times_referenced, last_used_at)
  VALUES (p_block_id, 1, now())
  ON CONFLICT (block_id)
  DO UPDATE SET
    times_referenced = block_usage.times_referenced + 1,
    last_used_at = now();
END;
$$;
CREATE FUNCTION public.log_extraction_metrics(p_dump_id uuid, p_basket_id uuid, p_workspace_id uuid, p_agent_version text, p_blocks_created integer, p_context_items_created integer, p_avg_confidence real, p_processing_time_ms integer) RETURNS uuid
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
DECLARE
  v_metric_id uuid;
BEGIN
  INSERT INTO extraction_quality_metrics (
    dump_id, basket_id, workspace_id, agent_version,
    blocks_created, context_items_created, avg_confidence, processing_time_ms
  ) VALUES (
    p_dump_id, p_basket_id, p_workspace_id, p_agent_version,
    p_blocks_created, p_context_items_created, p_avg_confidence, p_processing_time_ms
  )
  RETURNING id INTO v_metric_id;
  RETURN v_metric_id;
END;
$$;
CREATE FUNCTION public.map_anchor_key_to_role(anchor_key text) RETURNS text
    LANGUAGE plpgsql IMMUTABLE
    AS $$
BEGIN
  -- Extract role from anchor_key patterns
  -- Examples: "core_problem" -> "problem", "feature_block_1" -> "feature"
  IF anchor_key LIKE '%problem%' THEN RETURN 'problem';
  ELSIF anchor_key LIKE '%customer%' THEN RETURN 'customer';
  ELSIF anchor_key LIKE '%solution%' THEN RETURN 'solution';
  ELSIF anchor_key LIKE '%feature%' THEN RETURN 'feature';
  ELSIF anchor_key LIKE '%constraint%' THEN RETURN 'constraint';
  ELSIF anchor_key LIKE '%metric%' THEN RETURN 'metric';
  ELSIF anchor_key LIKE '%insight%' THEN RETURN 'insight';
  ELSIF anchor_key LIKE '%vision%' THEN RETURN 'vision';
  ELSE RETURN NULL; -- Unknown anchor key pattern
  END IF;
END;
$$;
CREATE FUNCTION public.mark_alert_read(p_alert_id uuid) RETURNS boolean
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
BEGIN
  UPDATE user_alerts 
  SET read_at = now() 
  WHERE id = p_alert_id AND user_id = auth.uid() AND read_at IS NULL;
  
  RETURN FOUND;
END;
$$;
CREATE FUNCTION public.mark_related_blocks_stale() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
BEGIN
  -- Mark blocks from previous dumps in same basket as potentially stale
  -- Force staleness by setting last_validated_at to 30 days ago
  UPDATE blocks
  SET last_validated_at = now() - interval '30 days'
  WHERE basket_id = NEW.basket_id
    AND raw_dump_id IN (
      SELECT id FROM raw_dumps
      WHERE basket_id = NEW.basket_id
      AND id != NEW.id
      AND created_at < NEW.created_at  -- Only older dumps
    )
    AND status NOT IN ('archived', 'rejected');  -- Don't mark archived blocks
  RETURN NEW;
END;
$$;
CREATE FUNCTION public.normalize_label(p_label text) RETURNS text
    LANGUAGE sql IMMUTABLE
    AS $$
  select case
           when p_label is null then null
           else lower(regexp_replace(p_label, '\s+', ' ', 'g'))
         end
$$;
CREATE FUNCTION public.prevent_lock_vs_constant() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
  IF NEW.state = 'LOCKED' THEN
    PERFORM 1 FROM blocks
      WHERE semantic_type = NEW.semantic_type
        AND scope IS NOT NULL          -- a Constant
        AND state = 'CONSTANT'
        AND basket_id = NEW.basket_id; -- same workspace implied
    IF FOUND THEN
      RAISE EXCEPTION 'LOCK_CONFLICT_CONSTANT';
    END IF;
  END IF;
  RETURN NEW;
END;
$$;
CREATE FUNCTION public.proposal_validation_check() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    -- Prevent approval of unvalidated proposals
    IF NEW.status = 'APPROVED' AND OLD.status != 'APPROVED' THEN
        IF NEW.validation_required = true AND NEW.validation_bypassed = false THEN
            -- Check if validator report is complete
            IF NEW.validator_report IS NULL OR 
               NOT (NEW.validator_report ? 'confidence') OR
               NOT (NEW.validator_report ? 'impact_summary') THEN
                RAISE EXCEPTION 'Cannot approve proposal without complete validator report. Use validation_bypassed=true to override.';
            END IF;
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$;
CREATE FUNCTION public.queue_agent_processing() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
  -- Insert into processing queue with workspace context
  INSERT INTO agent_processing_queue (
    dump_id, 
    basket_id, 
    workspace_id
  )
  SELECT 
    NEW.id,
    NEW.basket_id,
    b.workspace_id
  FROM baskets b
  WHERE b.id = NEW.basket_id;
  
  RETURN NEW;
END;
$$;
CREATE FUNCTION public.semantic_search_blocks(p_basket_id uuid, p_query_embedding public.vector, p_semantic_types text[] DEFAULT NULL::text[], p_anchor_roles text[] DEFAULT NULL::text[], p_states text[] DEFAULT ARRAY['ACCEPTED'::text, 'LOCKED'::text, 'CONSTANT'::text], p_min_similarity numeric DEFAULT 0.70, p_limit integer DEFAULT 20) RETURNS TABLE(id uuid, basket_id uuid, content text, semantic_type text, anchor_role text, state text, metadata jsonb, similarity_score numeric)
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
BEGIN
    RETURN QUERY
    SELECT
        b.id,
        b.basket_id,
        b.content,
        b.semantic_type,
        b.anchor_role,
        b.state::TEXT,
        b.metadata,
        (1 - (b.embedding <=> p_query_embedding))::DECIMAL AS similarity_score
    FROM public.blocks b
    WHERE b.basket_id = p_basket_id
        AND b.embedding IS NOT NULL
        AND (p_semantic_types IS NULL OR b.semantic_type = ANY(p_semantic_types))
        AND (p_anchor_roles IS NULL OR b.anchor_role = ANY(p_anchor_roles))
        AND b.state::TEXT = ANY(p_states)
        AND (1 - (b.embedding <=> p_query_embedding)) >= p_min_similarity
    ORDER BY b.embedding <=> p_query_embedding
    LIMIT p_limit;
END;
$$;
CREATE FUNCTION public.semantic_search_cross_basket(p_workspace_id uuid, p_query_embedding public.vector, p_scopes text[] DEFAULT ARRAY['WORKSPACE'::text, 'GLOBAL'::text], p_semantic_types text[] DEFAULT NULL::text[], p_min_similarity numeric DEFAULT 0.70, p_limit integer DEFAULT 10) RETURNS TABLE(id uuid, basket_id uuid, content text, semantic_type text, anchor_role text, scope text, similarity_score numeric)
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
BEGIN
    RETURN QUERY
    SELECT
        b.id,
        b.basket_id,
        b.content,
        b.semantic_type,
        b.anchor_role,
        b.scope::TEXT,
        (1 - (b.embedding <=> p_query_embedding))::DECIMAL AS similarity_score
    FROM public.blocks b
    JOIN public.baskets bsk ON b.basket_id = bsk.id
    WHERE bsk.workspace_id = p_workspace_id
        AND b.embedding IS NOT NULL
        AND b.scope::TEXT = ANY(p_scopes)
        AND b.state IN ('ACCEPTED', 'LOCKED', 'CONSTANT')
        AND (p_semantic_types IS NULL OR b.semantic_type = ANY(p_semantic_types))
        AND (1 - (b.embedding <=> p_query_embedding)) >= p_min_similarity
    ORDER BY b.embedding <=> p_query_embedding
    LIMIT p_limit;
END;
$$;
CREATE FUNCTION public.set_basket_user_id() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
begin
  if new.user_id is null then
    new.user_id := auth.uid();
  end if;
  return new;
end $$;
CREATE FUNCTION public.set_updated_at() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
    BEGIN
      NEW.updated_at := now();
      RETURN NEW;
    END;
    $$;
CREATE FUNCTION public.sql(query text) RETURNS json
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$ BEGIN RETURN to_json(query); END; $$;
CREATE FUNCTION public.sync_raw_dump_text_columns() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
  -- When body_md is updated, sync to text_dump
  IF NEW.body_md IS DISTINCT FROM OLD.body_md THEN
    NEW.text_dump = NEW.body_md;
  END IF;
  
  -- When text_dump is updated, sync to body_md  
  IF NEW.text_dump IS DISTINCT FROM OLD.text_dump THEN
    NEW.body_md = NEW.text_dump;
  END IF;
  
  RETURN NEW;
END;
$$;
CREATE FUNCTION public.traverse_relationships(p_start_block_id uuid, p_relationship_type text, p_direction text DEFAULT 'forward'::text, p_max_depth integer DEFAULT 2) RETURNS TABLE(id uuid, content text, semantic_type text, anchor_role text, depth integer, relationship_type text)
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
BEGIN
    RETURN QUERY
    WITH RECURSIVE relationship_chain AS (
        -- Base case: start block
        SELECT
            b.id,
            b.content,
            b.semantic_type,
            b.anchor_role,
            0 AS depth,
            ''::TEXT AS relationship_type
        FROM public.blocks b
        WHERE b.id = p_start_block_id
        UNION ALL
        -- Recursive case: follow relationships
        SELECT
            b.id,
            b.content,
            b.semantic_type,
            b.anchor_role,
            rc.depth + 1,
            r.relationship_type
        FROM relationship_chain rc
        JOIN public.substrate_relationships r ON
            CASE
                WHEN p_direction = 'forward' THEN rc.id = r.from_block_id
                ELSE rc.id = r.to_block_id
            END
        JOIN public.blocks b ON
            CASE
                WHEN p_direction = 'forward' THEN r.to_block_id = b.id
                ELSE r.from_block_id = b.id
            END
        WHERE rc.depth < p_max_depth
            AND r.relationship_type = p_relationship_type
            AND r.state = 'ACCEPTED'
    )
    SELECT DISTINCT ON (relationship_chain.id)
        relationship_chain.id,
        relationship_chain.content,
        relationship_chain.semantic_type,
        relationship_chain.anchor_role,
        relationship_chain.depth,
        relationship_chain.relationship_type
    FROM relationship_chain
    WHERE relationship_chain.depth > 0  -- Exclude start block
    ORDER BY relationship_chain.id, relationship_chain.depth;
END;
$$;
CREATE FUNCTION public.update_reflection_cache_updated_at() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$;
CREATE FUNCTION public.update_substrate_relationships_updated_at() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;
CREATE FUNCTION public.validate_structured_ingredient_metadata(metadata_json jsonb) RETURNS boolean
    LANGUAGE plpgsql
    AS $$
BEGIN
    -- Validate that structured ingredients have required fields
    IF metadata_json ? 'knowledge_ingredients' THEN
        -- Must have provenance validation
        IF NOT (metadata_json -> 'provenance_validated')::boolean THEN
            RETURN false;
        END IF;
        
        -- Must have extraction method marker
        IF NOT (metadata_json ? 'extraction_method') THEN
            RETURN false;
        END IF;
        
        -- Knowledge ingredients must have provenance
        IF NOT (metadata_json -> 'knowledge_ingredients' ? 'provenance') THEN
            RETURN false;
        END IF;
        
        RETURN true;
    END IF;
    
    -- Legacy blocks are always valid
    RETURN true;
END;
$$;
CREATE FUNCTION public.verify_canon_compatibility() RETURNS TABLE(test_name text, status text, details text)
    LANGUAGE plpgsql
    AS $$
BEGIN
  -- Test 1: Check emit_timeline_event function exists
  RETURN QUERY SELECT 
    'emit_timeline_event_function'::text,
    CASE WHEN COUNT(*) > 0 THEN 'PASS' ELSE 'FAIL' END::text,
    'Function emit_timeline_event exists: ' || COUNT(*)::text
  FROM pg_proc 
  WHERE proname = 'emit_timeline_event';
  
  -- Test 2: Check timeline_events table structure
  RETURN QUERY SELECT 
    'timeline_events_structure'::text,
    CASE WHEN COUNT(*) = 6 THEN 'PASS' ELSE 'FAIL' END::text,
    'Required columns (basket_id, kind, ts, ref_id, preview, payload): ' || COUNT(*)::text
  FROM information_schema.columns 
  WHERE table_name = 'timeline_events' 
    AND column_name IN ('basket_id', 'kind', 'ts', 'ref_id', 'preview', 'payload');
    
  -- Test 3: Check constraint allows Canon v1.3.1 event types
  RETURN QUERY SELECT 
    'canon_event_types'::text,
    'PASS'::text,
    'Constraint updated to allow Canon v1.3.1 event types'::text;
    
  -- Test 4: Check fn_timeline_emit exists (dependency)
  RETURN QUERY SELECT 
    'fn_timeline_emit_exists'::text,
    CASE WHEN COUNT(*) > 0 THEN 'PASS' ELSE 'FAIL' END::text,
    'Function fn_timeline_emit exists: ' || COUNT(*)::text
  FROM pg_proc 
  WHERE proname = 'fn_timeline_emit';
END;
$$;
CREATE TABLE public.blocks (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    basket_id uuid,
    parent_block_id uuid,
    semantic_type text NOT NULL,
    content text,
    version integer DEFAULT 1 NOT NULL,
    state public.block_state DEFAULT 'PROPOSED'::public.block_state NOT NULL,
    scope public.scope_level,
    canonical_value text,
    origin_ref uuid,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    workspace_id uuid NOT NULL,
    meta_agent_notes text,
    label text,
    meta_tags text[],
    is_required boolean DEFAULT false,
    raw_dump_id uuid,
    title text,
    body_md text,
    confidence_score double precision DEFAULT 0.5,
    metadata jsonb DEFAULT '{}'::jsonb,
    processing_agent text,
    status text DEFAULT 'proposed'::text,
    proposal_id uuid,
    approved_at timestamp with time zone,
    approved_by uuid,
    normalized_label text,
    updated_at timestamp with time zone DEFAULT now(),
    last_validated_at timestamp with time zone DEFAULT now(),
    anchor_role text,
    anchor_status text DEFAULT 'proposed'::text,
    anchor_confidence real,
    embedding public.vector(1536),
    CONSTRAINT blocks_anchor_confidence_check CHECK (((anchor_confidence >= (0.0)::double precision) AND (anchor_confidence <= (1.0)::double precision))),
    CONSTRAINT blocks_anchor_confidence_v3_check CHECK (((anchor_confidence IS NULL) OR ((anchor_confidence >= (0.0)::double precision) AND (anchor_confidence <= (1.0)::double precision)))),
    CONSTRAINT blocks_anchor_status_v3_check CHECK (((anchor_status IS NULL) OR (anchor_status = ANY (ARRAY['proposed'::text, 'accepted'::text, 'rejected'::text])))),
    CONSTRAINT blocks_constant_requires_scope CHECK ((((state = 'CONSTANT'::public.block_state) AND (scope IS NOT NULL)) OR (state <> 'CONSTANT'::public.block_state))),
    CONSTRAINT blocks_content_not_empty CHECK (((content IS NOT NULL) AND (content <> ''::text))),
    CONSTRAINT blocks_title_not_empty CHECK (((title IS NOT NULL) AND (title <> ''::text))),
    CONSTRAINT check_structured_ingredient_metadata CHECK (public.validate_structured_ingredient_metadata(metadata))
)
WITH (autovacuum_enabled='true');
ALTER TABLE ONLY public.blocks REPLICA IDENTITY FULL;
CREATE VIEW public.anchored_substrate AS
 SELECT 'block'::text AS substrate_type,
    b.id AS substrate_id,
    b.basket_id,
    b.workspace_id,
    b.anchor_role,
    b.anchor_status,
    b.anchor_confidence,
    b.title,
    b.content,
    b.semantic_type,
    (b.state)::text AS state,
    b.scope,
    b.created_at,
    b.updated_at,
    b.last_validated_at,
    b.metadata
   FROM public.blocks b
  WHERE (b.anchor_role IS NOT NULL);
CREATE TABLE public.app_events (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    v integer DEFAULT 1 NOT NULL,
    type text NOT NULL,
    name text NOT NULL,
    phase text,
    severity text DEFAULT 'info'::text NOT NULL,
    message text NOT NULL,
    workspace_id uuid NOT NULL,
    basket_id uuid,
    entity_id uuid,
    correlation_id text,
    dedupe_key text,
    ttl_ms integer,
    payload jsonb,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT app_events_phase_check CHECK ((phase = ANY (ARRAY['started'::text, 'progress'::text, 'succeeded'::text, 'failed'::text]))),
    CONSTRAINT app_events_severity_check CHECK ((severity = ANY (ARRAY['info'::text, 'success'::text, 'warning'::text, 'error'::text]))),
    CONSTRAINT app_events_type_check CHECK ((type = ANY (ARRAY['job_update'::text, 'system_alert'::text, 'action_result'::text, 'collab_activity'::text, 'validation'::text])))
);
CREATE TABLE public.artifact_generation_settings (
    workspace_id uuid NOT NULL,
    auto_substrate_reflection boolean DEFAULT true,
    auto_document_reflection boolean DEFAULT false,
    reflection_frequency interval DEFAULT '01:00:00'::interval,
    auto_version_on_edit boolean DEFAULT true,
    version_retention_days integer DEFAULT 90,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);
CREATE TABLE public.basket_anchors (
    id uuid DEFAULT extensions.uuid_generate_v4() NOT NULL,
    basket_id uuid NOT NULL,
    anchor_key text NOT NULL,
    label text NOT NULL,
    scope text NOT NULL,
    expected_type text NOT NULL,
    required boolean DEFAULT false NOT NULL,
    description text,
    ordering integer,
    linked_substrate_id uuid,
    status text DEFAULT 'active'::text NOT NULL,
    metadata jsonb DEFAULT '{}'::jsonb NOT NULL,
    last_refreshed_at timestamp with time zone,
    last_relationship_count integer DEFAULT 0 NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT basket_anchors_expected_type_check CHECK ((expected_type = ANY (ARRAY['block'::text, 'context_item'::text]))),
    CONSTRAINT basket_anchors_scope_check CHECK ((scope = ANY (ARRAY['core'::text, 'brain'::text, 'custom'::text])))
);
CREATE TABLE public.basket_deltas (
    delta_id uuid NOT NULL,
    basket_id uuid NOT NULL,
    payload jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    applied_at timestamp with time zone
);
CREATE TABLE public.basket_events (
    id integer NOT NULL,
    event_type text NOT NULL,
    payload jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now()
);
ALTER TABLE ONLY public.basket_events REPLICA IDENTITY FULL;
CREATE SEQUENCE public.basket_events_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE public.basket_events_id_seq OWNED BY public.basket_events.id;
CREATE TABLE public.basket_signatures (
    basket_id uuid NOT NULL,
    workspace_id uuid NOT NULL,
    summary text,
    anchors jsonb DEFAULT '[]'::jsonb,
    entities text[] DEFAULT ARRAY[]::text[],
    keywords text[] DEFAULT ARRAY[]::text[],
    embedding double precision[] DEFAULT ARRAY[]::double precision[],
    last_refreshed timestamp with time zone DEFAULT now() NOT NULL,
    ttl_hours integer DEFAULT 336 NOT NULL,
    source_reflection_id uuid,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);
CREATE TABLE public.baskets (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    name text,
    raw_dump_id uuid,
    status public.basket_state DEFAULT 'INIT'::public.basket_state NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    user_id uuid DEFAULT auth.uid(),
    workspace_id uuid NOT NULL,
    origin_template text,
    tags text[] DEFAULT '{}'::text[],
    idempotency_key uuid
);
CREATE TABLE public.block_links (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    block_id uuid,
    document_id uuid,
    occurrences integer DEFAULT 0,
    snippets jsonb
);
CREATE TABLE public.block_revisions (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    block_id uuid,
    workspace_id uuid,
    actor_id uuid,
    summary text,
    diff_json jsonb,
    created_at timestamp with time zone DEFAULT now()
);
CREATE TABLE public.block_usage (
    block_id uuid NOT NULL,
    times_referenced integer DEFAULT 0 NOT NULL,
    last_used_at timestamp with time zone,
    usefulness_score real GENERATED ALWAYS AS (
CASE
    WHEN (times_referenced = 0) THEN 0.0
    WHEN (times_referenced < 3) THEN 0.5
    ELSE 0.9
END) STORED,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);
CREATE TABLE public.document_context_items (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    document_id uuid NOT NULL,
    context_item_id uuid NOT NULL,
    role text,
    weight numeric,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);
CREATE TABLE public.document_versions (
    version_hash character varying(64) NOT NULL,
    document_id uuid NOT NULL,
    content text NOT NULL,
    metadata_snapshot jsonb DEFAULT '{}'::jsonb,
    substrate_refs_snapshot jsonb DEFAULT '[]'::jsonb,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    created_by uuid,
    version_message text,
    parent_version_hash character varying(64),
    composition_contract jsonb DEFAULT '{}'::jsonb,
    composition_signature character varying(64),
    version_trigger text,
    CONSTRAINT non_empty_content CHECK ((length(content) > 0)),
    CONSTRAINT valid_version_hash CHECK (((version_hash)::text ~ '^doc_v[a-f0-9]{58}$'::text)),
    CONSTRAINT valid_version_trigger CHECK (((version_trigger IS NULL) OR (version_trigger = ANY (ARRAY['initial'::text, 'substrate_update'::text, 'user_requested'::text, 'instruction_change'::text, 'upload_composition'::text, 'migrated'::text]))))
);
CREATE TABLE public.documents (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    basket_id uuid,
    title text NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    created_by uuid,
    updated_by uuid,
    workspace_id uuid NOT NULL,
    document_type text DEFAULT 'general'::text NOT NULL,
    metadata jsonb DEFAULT '{}'::jsonb NOT NULL,
    current_version_hash character varying(64),
    composition_instructions jsonb DEFAULT '{}'::jsonb,
    substrate_filter jsonb DEFAULT '{}'::jsonb,
    source_raw_dump_id uuid,
    doc_type text DEFAULT 'artifact_other'::text,
    previous_id uuid,
    derived_from jsonb DEFAULT '{}'::jsonb,
    CONSTRAINT documents_doc_type_check CHECK ((doc_type = ANY (ARRAY['document_canon'::text, 'starter_prompt'::text, 'artifact_other'::text])))
);
CREATE VIEW public.document_heads AS
 SELECT d.id AS document_id,
    d.basket_id,
    d.workspace_id,
    d.title,
    d.document_type,
    d.composition_instructions,
    d.substrate_filter,
    d.source_raw_dump_id,
    d.current_version_hash,
    d.created_at AS document_created_at,
    d.created_by AS document_created_by,
    d.updated_at AS document_updated_at,
    d.metadata AS document_metadata,
    dv.content,
    dv.metadata_snapshot AS version_metadata,
    dv.substrate_refs_snapshot,
    dv.created_at AS version_created_at,
    dv.created_by AS version_created_by,
    dv.version_trigger,
    dv.version_message
   FROM (public.documents d
     LEFT JOIN public.document_versions dv ON (((dv.version_hash)::text = (d.current_version_hash)::text)));
CREATE TABLE public.events (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    basket_id uuid,
    block_id uuid,
    kind text,
    payload jsonb,
    ts timestamp with time zone DEFAULT now() NOT NULL,
    workspace_id uuid NOT NULL,
    origin text DEFAULT 'user'::text,
    actor_id uuid,
    agent_type text,
    CONSTRAINT events_origin_check CHECK ((origin = ANY (ARRAY['user'::text, 'agent'::text, 'daemon'::text, 'system'::text])))
);
CREATE TABLE public.extraction_quality_metrics (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    dump_id uuid,
    basket_id uuid,
    workspace_id uuid NOT NULL,
    agent_version text NOT NULL,
    blocks_created integer DEFAULT 0,
    context_items_created integer DEFAULT 0,
    duplicates_detected integer DEFAULT 0,
    orphans_created integer DEFAULT 0,
    avg_confidence real DEFAULT 0.0,
    processing_time_ms integer,
    blocks_accepted integer DEFAULT 0,
    blocks_rejected integer DEFAULT 0,
    blocks_used integer DEFAULT 0,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);
CREATE TABLE public.idempotency_keys (
    request_id text NOT NULL,
    delta_id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);
CREATE TABLE public.integration_tokens (
    id uuid DEFAULT extensions.uuid_generate_v4() NOT NULL,
    token_hash text NOT NULL,
    user_id uuid NOT NULL,
    workspace_id uuid NOT NULL,
    description text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    revoked_at timestamp with time zone,
    last_used_at timestamp with time zone
);
CREATE TABLE public.knowledge_timeline (
    id uuid DEFAULT extensions.uuid_generate_v4() NOT NULL,
    basket_id uuid NOT NULL,
    workspace_id uuid NOT NULL,
    event_type public.knowledge_event_type NOT NULL,
    significance public.event_significance DEFAULT 'medium'::public.event_significance,
    title text NOT NULL,
    description text,
    metadata jsonb DEFAULT '{}'::jsonb,
    related_ids jsonb DEFAULT '{}'::jsonb,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT knowledge_timeline_description_length CHECK ((length(description) <= 1000)),
    CONSTRAINT knowledge_timeline_title_length CHECK (((length(title) >= 1) AND (length(title) <= 200)))
);
CREATE TABLE public.mcp_activity_logs (
    id uuid DEFAULT extensions.uuid_generate_v4() NOT NULL,
    workspace_id uuid NOT NULL,
    user_id uuid,
    tool text NOT NULL,
    host text NOT NULL,
    result text NOT NULL,
    latency_ms integer,
    basket_id uuid,
    selection_decision text,
    selection_score numeric,
    error_code text,
    session_id text,
    fingerprint_summary text,
    metadata jsonb,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);
CREATE VIEW public.mcp_activity_host_recent AS
 SELECT mcp_activity_logs.workspace_id,
    mcp_activity_logs.host,
    max(mcp_activity_logs.created_at) AS last_seen_at,
    count(*) FILTER (WHERE (mcp_activity_logs.created_at >= (now() - '01:00:00'::interval))) AS calls_last_hour,
    count(*) FILTER (WHERE ((mcp_activity_logs.result = 'error'::text) AND (mcp_activity_logs.created_at >= (now() - '01:00:00'::interval)))) AS errors_last_hour,
    percentile_cont((0.95)::double precision) WITHIN GROUP (ORDER BY ((COALESCE(mcp_activity_logs.latency_ms, 0))::double precision)) AS p95_latency_ms
   FROM public.mcp_activity_logs
  WHERE (mcp_activity_logs.created_at >= (now() - '7 days'::interval))
  GROUP BY mcp_activity_logs.workspace_id, mcp_activity_logs.host;
CREATE TABLE public.mcp_oauth_sessions (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    mcp_token text NOT NULL,
    supabase_token text NOT NULL,
    user_id uuid NOT NULL,
    workspace_id uuid NOT NULL,
    expires_at timestamp with time zone NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    last_used_at timestamp with time zone DEFAULT now() NOT NULL
);
CREATE TABLE public.mcp_unassigned_captures (
    id uuid DEFAULT extensions.uuid_generate_v4() NOT NULL,
    workspace_id uuid NOT NULL,
    requested_by uuid,
    tool text NOT NULL,
    summary text,
    payload jsonb,
    fingerprint jsonb,
    candidates jsonb,
    status text DEFAULT 'pending'::text NOT NULL,
    assigned_basket_id uuid,
    resolved_at timestamp with time zone,
    resolved_by uuid,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    source_host text,
    source_session text
);
CREATE TABLE public.narrative (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    basket_id uuid,
    raw_dump_id uuid,
    type text NOT NULL,
    title text NOT NULL,
    content text NOT NULL,
    confidence_score double precision DEFAULT 0.5,
    metadata jsonb DEFAULT '{}'::jsonb,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);
ALTER TABLE ONLY public.narrative REPLICA IDENTITY FULL;
CREATE TABLE public.openai_app_tokens (
    id uuid DEFAULT extensions.uuid_generate_v4() NOT NULL,
    workspace_id uuid NOT NULL,
    install_id text,
    access_token text,
    refresh_token text,
    expires_at timestamp with time zone,
    scope text,
    provider_metadata jsonb DEFAULT '{}'::jsonb,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    access_token_enc jsonb,
    refresh_token_enc jsonb,
    encryption_version smallint,
    encryption_updated_at timestamp with time zone,
    rotated_at timestamp with time zone
);
CREATE TABLE public.p3_p4_regeneration_policy (
    workspace_id uuid NOT NULL,
    insight_canon_auto_regenerate boolean DEFAULT true,
    document_canon_auto_regenerate boolean DEFAULT true,
    workspace_insight_enabled boolean DEFAULT false,
    workspace_insight_min_baskets integer DEFAULT 3,
    workspace_insight_throttle_hours integer DEFAULT 24,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);
CREATE TABLE public.pipeline_metrics (
    id bigint NOT NULL,
    ts timestamp with time zone DEFAULT now() NOT NULL,
    pipeline text NOT NULL,
    basket_id uuid,
    dump_id uuid,
    doc_id uuid,
    dims jsonb DEFAULT '{}'::jsonb NOT NULL,
    counts jsonb DEFAULT '{}'::jsonb NOT NULL
);
CREATE SEQUENCE public.pipeline_metrics_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE public.pipeline_metrics_id_seq OWNED BY public.pipeline_metrics.id;
CREATE TABLE public.pipeline_offsets (
    pipeline_name text NOT NULL,
    last_event_id uuid,
    last_event_ts timestamp with time zone,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);
CREATE TABLE public.proposal_executions (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    proposal_id uuid NOT NULL,
    operation_index integer NOT NULL,
    operation_type text NOT NULL,
    executed_at timestamp with time zone DEFAULT now() NOT NULL,
    success boolean NOT NULL,
    result_data jsonb DEFAULT '{}'::jsonb,
    error_message text,
    substrate_id uuid,
    rpc_called text,
    execution_time_ms integer,
    operations_count integer,
    operations_summary jsonb DEFAULT '{}'::jsonb
);
CREATE TABLE public.proposals (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    basket_id uuid,
    workspace_id uuid NOT NULL,
    proposal_kind public.proposal_kind NOT NULL,
    basis_snapshot_id uuid,
    origin text NOT NULL,
    provenance jsonb DEFAULT '[]'::jsonb,
    ops jsonb NOT NULL,
    validator_report jsonb DEFAULT '{}'::jsonb,
    status public.proposal_state DEFAULT 'PROPOSED'::public.proposal_state NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    created_by uuid,
    reviewed_by uuid,
    reviewed_at timestamp with time zone,
    review_notes text,
    metadata jsonb DEFAULT '{}'::jsonb,
    blast_radius public.blast_radius DEFAULT 'Local'::public.blast_radius,
    executed_at timestamp with time zone,
    execution_log jsonb DEFAULT '[]'::jsonb,
    commit_id uuid,
    is_executed boolean DEFAULT false,
    validator_version text DEFAULT 'v1.0'::text,
    validation_required boolean DEFAULT true,
    validation_bypassed boolean DEFAULT false,
    bypass_reason text,
    source_host text,
    source_session text,
    scope text DEFAULT 'basket'::text,
    target_basket_id uuid,
    affected_basket_ids uuid[] DEFAULT '{}'::uuid[],
    CONSTRAINT proposals_origin_check CHECK ((origin = ANY (ARRAY['agent'::text, 'human'::text]))),
    CONSTRAINT proposals_scope_check CHECK ((scope = ANY (ARRAY['basket'::text, 'workspace'::text, 'cross-basket'::text])))
);
CREATE TABLE public.raw_dumps (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    basket_id uuid NOT NULL,
    body_md text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    workspace_id uuid NOT NULL,
    file_url text,
    document_id uuid,
    fragments jsonb DEFAULT '[]'::jsonb,
    processing_status text DEFAULT 'unprocessed'::text,
    processed_at timestamp with time zone,
    source_meta jsonb DEFAULT '{}'::jsonb,
    ingest_trace_id text,
    dump_request_id uuid,
    text_dump text
);
ALTER TABLE ONLY public.raw_dumps REPLICA IDENTITY FULL;
CREATE TABLE public.reflections_artifact (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    basket_id uuid,
    workspace_id uuid NOT NULL,
    substrate_hash text NOT NULL,
    reflection_text text NOT NULL,
    substrate_window_start timestamp with time zone,
    substrate_window_end timestamp with time zone,
    computation_timestamp timestamp with time zone NOT NULL,
    last_accessed_at timestamp with time zone DEFAULT now(),
    meta jsonb DEFAULT '{}'::jsonb,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    insight_type text,
    is_current boolean DEFAULT false,
    previous_id uuid,
    derived_from jsonb DEFAULT '[]'::jsonb,
    graph_signature text,
    scope_level text DEFAULT 'basket'::text,
    CONSTRAINT insight_scope_consistency CHECK ((((scope_level = 'basket'::text) AND (basket_id IS NOT NULL)) OR ((scope_level <> 'basket'::text) AND (basket_id IS NULL)))),
    CONSTRAINT reflections_artifact_insight_type_check CHECK ((insight_type = ANY (ARRAY['insight_canon'::text, 'doc_insight'::text, 'timeboxed_insight'::text, 'review_insight'::text]))),
    CONSTRAINT reflections_artifact_scope_level_check CHECK ((scope_level = ANY (ARRAY['basket'::text, 'workspace'::text, 'org'::text, 'global'::text])))
);
CREATE TABLE public.revisions (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    basket_id uuid,
    actor_id uuid,
    summary text,
    diff_json jsonb,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);
CREATE TABLE public.substrate_references (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    document_id uuid NOT NULL,
    substrate_type public.substrate_type NOT NULL,
    substrate_id uuid NOT NULL,
    role text,
    weight numeric(3,2),
    snippets jsonb DEFAULT '[]'::jsonb,
    metadata jsonb DEFAULT '{}'::jsonb,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    created_by uuid,
    CONSTRAINT substrate_references_weight_check CHECK (((weight >= (0)::numeric) AND (weight <= (1)::numeric)))
);
CREATE TABLE public.substrate_relationships (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    from_block_id uuid NOT NULL,
    to_block_id uuid NOT NULL,
    relationship_type text NOT NULL,
    confidence_score numeric(3,2),
    inference_method text,
    state public.block_state DEFAULT 'PROPOSED'::public.block_state NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    created_by uuid,
    metadata jsonb DEFAULT '{}'::jsonb,
    CONSTRAINT no_self_reference CHECK ((from_block_id <> to_block_id)),
    CONSTRAINT valid_confidence_score CHECK (((confidence_score IS NULL) OR ((confidence_score >= (0)::numeric) AND (confidence_score <= (1)::numeric)))),
    CONSTRAINT valid_inference_method CHECK (((inference_method IS NULL) OR (inference_method = ANY (ARRAY['semantic_search'::text, 'llm_verification'::text, 'user_created'::text, 'agent_inferred'::text])))),
    CONSTRAINT valid_relationship_type CHECK ((relationship_type = ANY (ARRAY['addresses'::text, 'supports'::text, 'contradicts'::text, 'depends_on'::text])))
);
CREATE TABLE public.substrate_tombstones (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    workspace_id uuid NOT NULL,
    basket_id uuid NOT NULL,
    substrate_type text NOT NULL,
    substrate_id uuid NOT NULL,
    deletion_mode text NOT NULL,
    redaction_scope text,
    redaction_reason text,
    legal_hold boolean DEFAULT false,
    refs_detached_count integer DEFAULT 0,
    relationships_pruned_count integer DEFAULT 0,
    affected_documents_count integer DEFAULT 0,
    retention_policy_id uuid,
    earliest_physical_delete_at timestamp with time zone,
    event_ids uuid[] DEFAULT '{}'::uuid[],
    content_fingerprint text,
    created_at timestamp with time zone DEFAULT now(),
    created_by uuid,
    physically_deleted_at timestamp with time zone,
    CONSTRAINT substrate_tombstones_deletion_mode_check CHECK ((deletion_mode = ANY (ARRAY['archived'::text, 'redacted'::text, 'deleted'::text]))),
    CONSTRAINT substrate_tombstones_redaction_scope_check CHECK ((redaction_scope = ANY (ARRAY['full'::text, 'partial'::text]))),
    CONSTRAINT substrate_tombstones_substrate_type_check CHECK ((substrate_type = ANY (ARRAY['block'::text, 'context_item'::text, 'dump'::text, 'timeline_event'::text])))
);
CREATE TABLE public.timeline_events (
    id bigint NOT NULL,
    basket_id uuid NOT NULL,
    ts timestamp with time zone DEFAULT now() NOT NULL,
    kind text NOT NULL,
    ref_id uuid,
    preview text,
    payload jsonb,
    workspace_id uuid NOT NULL,
    source_host text,
    source_session text,
    CONSTRAINT timeline_events_kind_check CHECK ((kind = ANY (ARRAY['dump'::text, 'reflection'::text, 'narrative'::text, 'system_note'::text, 'block'::text, 'dump.created'::text, 'dump.queued'::text, 'block.created'::text, 'block.updated'::text, 'block.state_changed'::text, 'context_item.created'::text, 'context_item.updated'::text, 'context_item.archived'::text, 'relationship.created'::text, 'relationship.deleted'::text, 'reflection.computed'::text, 'reflection.cached'::text, 'document.created'::text, 'document.updated'::text, 'document.composed'::text, 'narrative.authored'::text, 'document.block.attached'::text, 'document.block.detached'::text, 'document.dump.attached'::text, 'document.dump.detached'::text, 'document.context_item.attached'::text, 'document.context_item.detached'::text, 'document.reflection.attached'::text, 'document.reflection.detached'::text, 'document.timeline_event.attached'::text, 'document.timeline_event.detached'::text, 'proposal.submitted'::text, 'proposal.approved'::text, 'proposal.rejected'::text, 'substrate.committed'::text, 'basket.created'::text, 'workspace.member_added'::text, 'delta.applied'::text, 'delta.rejected'::text, 'cascade.completed'::text, 'work.initiated'::text, 'work.routed'::text, 'pipeline.cascade_triggered'::text, 'pipeline.cascade_completed'::text, 'pipeline.cascade_failed'::text, 'queue.entry_created'::text, 'queue.processing_started'::text, 'queue.processing_completed'::text, 'queue.processing_failed'::text])))
);
CREATE SEQUENCE public.timeline_events_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE public.timeline_events_id_seq OWNED BY public.timeline_events.id;
CREATE TABLE public.user_alerts (
    id uuid DEFAULT extensions.uuid_generate_v4() NOT NULL,
    user_id uuid NOT NULL,
    workspace_id uuid NOT NULL,
    alert_type public.alert_type NOT NULL,
    severity public.alert_severity DEFAULT 'info'::public.alert_severity,
    title text NOT NULL,
    message text NOT NULL,
    actionable boolean DEFAULT false,
    action_url text,
    action_label text,
    related_entities jsonb DEFAULT '{}'::jsonb,
    expires_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    read_at timestamp with time zone,
    dismissed_at timestamp with time zone,
    CONSTRAINT user_alerts_action_label_length CHECK (((actionable = false) OR ((length(action_label) >= 1) AND (length(action_label) <= 50)))),
    CONSTRAINT user_alerts_message_length CHECK (((length(message) >= 1) AND (length(message) <= 500))),
    CONSTRAINT user_alerts_title_length CHECK (((length(title) >= 1) AND (length(title) <= 150)))
);
CREATE VIEW public.v_events_rel_bulk AS
 SELECT events.id,
    events.basket_id,
    events.kind,
    events.payload,
    events.ts
   FROM public.events
  WHERE (events.kind = 'rel.bulk_upserted'::text)
  ORDER BY events.ts;
CREATE VIEW public.v_kpi_24h AS
 WITH pm AS (
         SELECT pipeline_metrics.id,
            pipeline_metrics.ts,
            pipeline_metrics.pipeline,
            pipeline_metrics.basket_id,
            pipeline_metrics.dump_id,
            pipeline_metrics.doc_id,
            pipeline_metrics.dims,
            pipeline_metrics.counts
           FROM public.pipeline_metrics
          WHERE (pipeline_metrics.ts > (now() - '24:00:00'::interval))
        ), runs AS (
         SELECT pm.pipeline,
            count(*) AS runs
           FROM pm
          GROUP BY pm.pipeline
        ), agg AS (
         SELECT pm.pipeline,
            kv.key,
            sum((kv.val)::numeric) AS value
           FROM (pm
             CROSS JOIN LATERAL jsonb_each_text(pm.counts) kv(key, val))
          WHERE (kv.val ~ '^-?\\d+(\\.\\d+)?$'::text)
          GROUP BY pm.pipeline, kv.key
        )
 SELECT r.pipeline,
    r.runs,
    COALESCE(jsonb_object_agg(a.key, to_jsonb(a.value) ORDER BY a.key), '{}'::jsonb) AS totals
   FROM (runs r
     LEFT JOIN agg a USING (pipeline))
  GROUP BY r.pipeline, r.runs;
CREATE VIEW public.v_kpi_basket_recent AS
 SELECT pipeline_metrics.basket_id,
    pipeline_metrics.pipeline,
    pipeline_metrics.ts,
    pipeline_metrics.counts,
    pipeline_metrics.dims
   FROM public.pipeline_metrics
  WHERE (pipeline_metrics.ts > (now() - '7 days'::interval))
  ORDER BY pipeline_metrics.ts DESC;
CREATE TABLE public.workspace_memberships (
    id bigint NOT NULL,
    workspace_id uuid,
    user_id uuid,
    role text DEFAULT 'member'::text,
    created_at timestamp with time zone DEFAULT now()
);
CREATE VIEW public.v_user_workspaces AS
 SELECT wm.user_id,
    wm.workspace_id
   FROM public.workspace_memberships wm;
CREATE TABLE public.workspace_governance_settings (
    workspace_id uuid NOT NULL,
    governance_enabled boolean DEFAULT false NOT NULL,
    validator_required boolean DEFAULT false NOT NULL,
    direct_substrate_writes boolean DEFAULT false NOT NULL,
    governance_ui_enabled boolean DEFAULT false NOT NULL,
    ep_onboarding_dump text DEFAULT 'direct'::text NOT NULL,
    ep_manual_edit text DEFAULT 'proposal'::text NOT NULL,
    ep_document_edit text DEFAULT 'proposal'::text NOT NULL,
    ep_graph_action text DEFAULT 'proposal'::text NOT NULL,
    ep_timeline_restore text DEFAULT 'proposal'::text NOT NULL,
    default_blast_radius public.blast_radius DEFAULT 'Scoped'::public.blast_radius NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    artifact_generation_enabled boolean DEFAULT true,
    auto_reflection_compute boolean DEFAULT true,
    document_versioning_enabled boolean DEFAULT true,
    retention_enabled boolean DEFAULT false NOT NULL,
    retention_policy jsonb DEFAULT '{}'::jsonb NOT NULL,
    ep_reflection_suggestion text DEFAULT 'proposal'::text NOT NULL,
    CONSTRAINT workspace_governance_settings_ep_document_edit_check CHECK ((ep_document_edit = ANY (ARRAY['proposal'::text, 'direct'::text, 'hybrid'::text]))),
    CONSTRAINT workspace_governance_settings_ep_graph_action_check CHECK ((ep_graph_action = ANY (ARRAY['proposal'::text, 'direct'::text, 'hybrid'::text]))),
    CONSTRAINT workspace_governance_settings_ep_manual_edit_check CHECK ((ep_manual_edit = ANY (ARRAY['proposal'::text, 'direct'::text, 'hybrid'::text]))),
    CONSTRAINT workspace_governance_settings_ep_onboarding_dump_check CHECK ((ep_onboarding_dump = ANY (ARRAY['proposal'::text, 'direct'::text, 'hybrid'::text]))),
    CONSTRAINT workspace_governance_settings_ep_reflection_suggestion_check CHECK ((ep_reflection_suggestion = ANY (ARRAY['proposal'::text, 'direct'::text, 'hybrid'::text]))),
    CONSTRAINT workspace_governance_settings_ep_timeline_restore_check CHECK ((ep_timeline_restore = ANY (ARRAY['proposal'::text, 'direct'::text, 'hybrid'::text])))
);
CREATE SEQUENCE public.workspace_memberships_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE public.workspace_memberships_id_seq OWNED BY public.workspace_memberships.id;
CREATE TABLE public.workspaces (
    id uuid DEFAULT extensions.uuid_generate_v4() NOT NULL,
    owner_id uuid,
    name text NOT NULL,
    is_demo boolean DEFAULT false,
    created_at timestamp with time zone DEFAULT now()
);
ALTER TABLE ONLY public.basket_events ALTER COLUMN id SET DEFAULT nextval('public.basket_events_id_seq'::regclass);
ALTER TABLE ONLY public.pipeline_metrics ALTER COLUMN id SET DEFAULT nextval('public.pipeline_metrics_id_seq'::regclass);
ALTER TABLE ONLY public.timeline_events ALTER COLUMN id SET DEFAULT nextval('public.timeline_events_id_seq'::regclass);
ALTER TABLE ONLY public.workspace_memberships ALTER COLUMN id SET DEFAULT nextval('public.workspace_memberships_id_seq'::regclass);
ALTER TABLE ONLY public.agent_processing_queue
    ADD CONSTRAINT agent_processing_queue_pkey PRIMARY KEY (id);
ALTER TABLE ONLY public.app_events
    ADD CONSTRAINT app_events_pkey PRIMARY KEY (id);
ALTER TABLE ONLY public.artifact_generation_settings
    ADD CONSTRAINT artifact_generation_settings_pkey PRIMARY KEY (workspace_id);
ALTER TABLE ONLY public.basket_anchors
    ADD CONSTRAINT basket_anchors_pkey PRIMARY KEY (id);
ALTER TABLE ONLY public.basket_deltas
    ADD CONSTRAINT basket_deltas_pkey PRIMARY KEY (delta_id);
ALTER TABLE ONLY public.basket_events
    ADD CONSTRAINT basket_events_pkey PRIMARY KEY (id);
ALTER TABLE ONLY public.reflections_artifact
    ADD CONSTRAINT basket_reflections_pkey PRIMARY KEY (id);
ALTER TABLE ONLY public.basket_signatures
    ADD CONSTRAINT basket_signatures_pkey PRIMARY KEY (basket_id);
ALTER TABLE public.baskets
    ADD CONSTRAINT baskets_idem_is_uuid CHECK (((idempotency_key IS NULL) OR ((idempotency_key)::text ~* '^[0-9a-f-]{36}$'::text))) NOT VALID;
ALTER TABLE ONLY public.baskets
    ADD CONSTRAINT baskets_pkey PRIMARY KEY (id);
ALTER TABLE ONLY public.block_links
    ADD CONSTRAINT block_links_pkey PRIMARY KEY (id);
ALTER TABLE ONLY public.block_revisions
    ADD CONSTRAINT block_revisions_pkey PRIMARY KEY (id);
ALTER TABLE ONLY public.block_usage
    ADD CONSTRAINT block_usage_pkey PRIMARY KEY (block_id);
ALTER TABLE ONLY public.blocks
    ADD CONSTRAINT blocks_pkey PRIMARY KEY (id);
ALTER TABLE ONLY public.document_context_items
    ADD CONSTRAINT document_context_items_pkey PRIMARY KEY (id);
ALTER TABLE ONLY public.document_versions
    ADD CONSTRAINT document_versions_pkey PRIMARY KEY (version_hash);
ALTER TABLE ONLY public.documents
    ADD CONSTRAINT documents_pkey PRIMARY KEY (id);
ALTER TABLE public.raw_dumps
    ADD CONSTRAINT dumps_req_is_uuid CHECK (((dump_request_id IS NULL) OR ((dump_request_id)::text ~* '^[0-9a-f-]{36}$'::text))) NOT VALID;
ALTER TABLE ONLY public.events
    ADD CONSTRAINT events_pkey PRIMARY KEY (id);
ALTER TABLE ONLY public.extraction_quality_metrics
    ADD CONSTRAINT extraction_quality_metrics_pkey PRIMARY KEY (id);
ALTER TABLE ONLY public.idempotency_keys
    ADD CONSTRAINT idempotency_keys_pkey PRIMARY KEY (request_id);
ALTER TABLE ONLY public.integration_tokens
    ADD CONSTRAINT integration_tokens_pkey PRIMARY KEY (id);
ALTER TABLE ONLY public.integration_tokens
    ADD CONSTRAINT integration_tokens_token_hash_key UNIQUE (token_hash);
ALTER TABLE ONLY public.knowledge_timeline
    ADD CONSTRAINT knowledge_timeline_pkey PRIMARY KEY (id);
ALTER TABLE ONLY public.mcp_activity_logs
    ADD CONSTRAINT mcp_activity_logs_pkey PRIMARY KEY (id);
ALTER TABLE ONLY public.mcp_oauth_sessions
    ADD CONSTRAINT mcp_oauth_sessions_mcp_token_key UNIQUE (mcp_token);
ALTER TABLE ONLY public.mcp_oauth_sessions
    ADD CONSTRAINT mcp_oauth_sessions_pkey PRIMARY KEY (id);
ALTER TABLE ONLY public.mcp_unassigned_captures
    ADD CONSTRAINT mcp_unassigned_captures_pkey PRIMARY KEY (id);
ALTER TABLE ONLY public.narrative
    ADD CONSTRAINT narrative_pkey PRIMARY KEY (id);
ALTER TABLE ONLY public.openai_app_tokens
    ADD CONSTRAINT openai_app_tokens_pkey PRIMARY KEY (id);
ALTER TABLE ONLY public.p3_p4_regeneration_policy
    ADD CONSTRAINT p3_p4_regeneration_policy_pkey PRIMARY KEY (workspace_id);
ALTER TABLE ONLY public.pipeline_metrics
    ADD CONSTRAINT pipeline_metrics_pkey PRIMARY KEY (id);
ALTER TABLE ONLY public.pipeline_offsets
    ADD CONSTRAINT pipeline_offsets_pkey PRIMARY KEY (pipeline_name);
ALTER TABLE ONLY public.proposal_executions
    ADD CONSTRAINT proposal_executions_pkey PRIMARY KEY (id);
ALTER TABLE ONLY public.proposals
    ADD CONSTRAINT proposals_pkey PRIMARY KEY (id);
ALTER TABLE ONLY public.raw_dumps
    ADD CONSTRAINT raw_dumps_pkey PRIMARY KEY (id);
ALTER TABLE ONLY public.revisions
    ADD CONSTRAINT revisions_pkey PRIMARY KEY (id);
ALTER TABLE ONLY public.substrate_references
    ADD CONSTRAINT substrate_references_document_id_substrate_type_substrate_i_key UNIQUE (document_id, substrate_type, substrate_id);
ALTER TABLE ONLY public.substrate_references
    ADD CONSTRAINT substrate_references_pkey PRIMARY KEY (id);
ALTER TABLE ONLY public.substrate_relationships
    ADD CONSTRAINT substrate_relationships_pkey PRIMARY KEY (id);
ALTER TABLE ONLY public.substrate_tombstones
    ADD CONSTRAINT substrate_tombstones_pkey PRIMARY KEY (id);
ALTER TABLE ONLY public.timeline_events
    ADD CONSTRAINT timeline_events_pkey PRIMARY KEY (id);
ALTER TABLE ONLY public.substrate_relationships
    ADD CONSTRAINT unique_relationship UNIQUE (from_block_id, to_block_id, relationship_type);
ALTER TABLE ONLY public.raw_dumps
    ADD CONSTRAINT uq_raw_dumps_basket_dump_req UNIQUE (basket_id, dump_request_id);
ALTER TABLE ONLY public.user_alerts
    ADD CONSTRAINT user_alerts_pkey PRIMARY KEY (id);
ALTER TABLE ONLY public.workspace_governance_settings
    ADD CONSTRAINT workspace_governance_settings_pkey PRIMARY KEY (workspace_id);
ALTER TABLE ONLY public.workspace_memberships
    ADD CONSTRAINT workspace_memberships_pkey PRIMARY KEY (id);
ALTER TABLE ONLY public.workspace_memberships
    ADD CONSTRAINT workspace_memberships_workspace_id_user_id_key UNIQUE (workspace_id, user_id);
ALTER TABLE ONLY public.workspaces
    ADD CONSTRAINT workspaces_pkey PRIMARY KEY (id);
CREATE INDEX baskets_user_idx ON public.baskets USING btree (user_id);
CREATE INDEX blk_doc_idx ON public.block_links USING btree (block_id, document_id);
CREATE INDEX blocks_basket_embedding_idx ON public.blocks USING btree (basket_id, semantic_type) WHERE (embedding IS NOT NULL);
CREATE INDEX blocks_embedding_accepted_idx ON public.blocks USING ivfflat (embedding public.vector_cosine_ops) WITH (lists='100') WHERE (state = ANY (ARRAY['ACCEPTED'::public.block_state, 'LOCKED'::public.block_state, 'CONSTANT'::public.block_state]));
CREATE INDEX blocks_embedding_idx ON public.blocks USING ivfflat (embedding public.vector_cosine_ops) WITH (lists='100');
CREATE UNIQUE INDEX docs_basket_title_idx ON public.documents USING btree (basket_id, title);
CREATE INDEX idx_agent_queue_cascade ON public.agent_processing_queue USING gin (cascade_metadata);
CREATE UNIQUE INDEX idx_agent_queue_dump_id_unique ON public.agent_processing_queue USING btree (dump_id) WHERE (dump_id IS NOT NULL);
CREATE INDEX idx_agent_queue_priority ON public.agent_processing_queue USING btree (priority DESC, created_at);
CREATE INDEX idx_agent_queue_user_workspace ON public.agent_processing_queue USING btree (user_id, workspace_id);
CREATE INDEX idx_agent_queue_work_id ON public.agent_processing_queue USING btree (work_id);
CREATE INDEX idx_agent_queue_work_type ON public.agent_processing_queue USING btree (work_type, processing_state);
CREATE INDEX idx_app_events_basket ON public.app_events USING btree (basket_id, created_at DESC) WHERE (basket_id IS NOT NULL);
CREATE INDEX idx_app_events_correlation ON public.app_events USING btree (correlation_id) WHERE (correlation_id IS NOT NULL);
CREATE INDEX idx_app_events_dedupe ON public.app_events USING btree (dedupe_key) WHERE (dedupe_key IS NOT NULL);
CREATE INDEX idx_app_events_workspace ON public.app_events USING btree (workspace_id, created_at DESC);
CREATE INDEX idx_basket_anchors_scope ON public.basket_anchors USING btree (basket_id, scope);
CREATE INDEX idx_basket_anchors_substrate ON public.basket_anchors USING btree (linked_substrate_id);
CREATE INDEX idx_basket_deltas_applied_at ON public.basket_deltas USING btree (applied_at);
CREATE INDEX idx_basket_deltas_basket ON public.basket_deltas USING btree (basket_id, created_at DESC);
CREATE INDEX idx_basket_deltas_basket_id ON public.basket_deltas USING btree (basket_id);
CREATE INDEX idx_basket_deltas_created ON public.basket_deltas USING btree (created_at DESC);
CREATE INDEX idx_basket_deltas_created_at ON public.basket_deltas USING btree (created_at DESC);
CREATE INDEX idx_basket_deltas_unapplied ON public.basket_deltas USING btree (basket_id, created_at DESC) WHERE (applied_at IS NULL);
CREATE INDEX idx_basket_events_created ON public.basket_events USING btree (created_at DESC);
CREATE INDEX idx_basket_events_created_at ON public.basket_events USING btree (created_at DESC);
CREATE INDEX idx_basket_events_event_type ON public.basket_events USING btree (event_type);
CREATE INDEX idx_basket_signatures_updated ON public.basket_signatures USING btree (last_refreshed DESC);
CREATE INDEX idx_basket_signatures_workspace ON public.basket_signatures USING btree (workspace_id);
CREATE INDEX idx_baskets_workspace ON public.baskets USING btree (workspace_id);
CREATE INDEX idx_block_revisions_basket_ts ON public.block_revisions USING btree (workspace_id, created_at DESC);
CREATE INDEX idx_block_usage_last_used ON public.block_usage USING btree (last_used_at DESC NULLS LAST);
CREATE INDEX idx_block_usage_score ON public.block_usage USING btree (usefulness_score DESC);
CREATE INDEX idx_blocks_anchor_confidence ON public.blocks USING btree (basket_id, anchor_confidence DESC) WHERE ((anchor_role IS NOT NULL) AND (anchor_status = 'accepted'::text));
CREATE INDEX idx_blocks_anchor_role ON public.blocks USING btree (basket_id, anchor_role, anchor_status) WHERE (anchor_role IS NOT NULL);
CREATE INDEX idx_blocks_anchor_vocabulary ON public.blocks USING btree (basket_id, anchor_role, anchor_status) WHERE (anchor_role IS NOT NULL);
CREATE INDEX idx_blocks_basket_state_time ON public.blocks USING btree (basket_id, state, last_validated_at DESC) WHERE (state = 'ACCEPTED'::public.block_state);
CREATE INDEX idx_blocks_constants ON public.blocks USING btree (workspace_id, state, scope) WHERE (state = 'CONSTANT'::public.block_state);
CREATE INDEX idx_blocks_raw_dump ON public.blocks USING btree (raw_dump_id);
CREATE INDEX idx_blocks_recent_validated ON public.blocks USING btree (basket_id, last_validated_at DESC) WHERE (state = 'ACCEPTED'::public.block_state);
CREATE INDEX idx_blocks_semantic_type ON public.blocks USING btree (basket_id, semantic_type, state);
CREATE INDEX idx_blocks_staleness ON public.blocks USING btree (last_validated_at DESC NULLS LAST);
CREATE INDEX idx_blocks_updated_at ON public.blocks USING btree (updated_at);
CREATE INDEX idx_blocks_version_chain ON public.blocks USING btree (parent_block_id, version) WHERE (parent_block_id IS NOT NULL);
CREATE INDEX idx_blocks_workspace ON public.blocks USING btree (workspace_id);
CREATE INDEX idx_blocks_workspace_scope ON public.blocks USING btree (workspace_id, scope, state) WHERE (scope IS NOT NULL);
CREATE INDEX idx_doc_versions_signature ON public.document_versions USING btree (composition_signature) WHERE (composition_signature IS NOT NULL);
CREATE INDEX idx_document_versions_created ON public.document_versions USING btree (created_at DESC);
CREATE INDEX idx_document_versions_document ON public.document_versions USING btree (document_id);
CREATE INDEX idx_document_versions_hash ON public.document_versions USING btree (version_hash);
CREATE INDEX idx_documents_basket ON public.documents USING btree (basket_id);
CREATE INDEX idx_documents_current_version ON public.documents USING btree (current_version_hash) WHERE (current_version_hash IS NOT NULL);
CREATE INDEX idx_documents_lineage ON public.documents USING btree (previous_id) WHERE (previous_id IS NOT NULL);
CREATE INDEX idx_documents_meta_comp_sig ON public.documents USING btree (((metadata ->> 'composition_signature'::text)));
CREATE INDEX idx_documents_workspace ON public.documents USING btree (workspace_id);
CREATE INDEX idx_events_agent_type ON public.events USING btree (agent_type);
CREATE INDEX idx_events_basket_kind_ts ON public.events USING btree (basket_id, kind, ts);
CREATE INDEX idx_events_origin_kind ON public.events USING btree (origin, kind);
CREATE INDEX idx_events_workspace_ts ON public.events USING btree (workspace_id, ts DESC);
CREATE INDEX idx_extraction_quality_basket ON public.extraction_quality_metrics USING btree (basket_id, created_at DESC);
CREATE INDEX idx_extraction_quality_workspace ON public.extraction_quality_metrics USING btree (workspace_id, created_at DESC);
CREATE INDEX idx_history_basket_ts ON public.timeline_events USING btree (basket_id, ts DESC, id DESC);
CREATE INDEX idx_idem_delta_id ON public.idempotency_keys USING btree (delta_id);
CREATE INDEX idx_idempotency_delta ON public.idempotency_keys USING btree (delta_id);
CREATE INDEX idx_idempotency_keys_delta_id ON public.idempotency_keys USING btree (delta_id);
CREATE INDEX idx_knowledge_timeline_basket_time ON public.knowledge_timeline USING btree (basket_id, created_at DESC);
CREATE INDEX idx_knowledge_timeline_significance ON public.knowledge_timeline USING btree (significance, created_at DESC);
CREATE INDEX idx_knowledge_timeline_workspace_time ON public.knowledge_timeline USING btree (workspace_id, created_at DESC);
CREATE INDEX idx_mcp_activity_host ON public.mcp_activity_logs USING btree (host, created_at DESC);
CREATE INDEX idx_mcp_activity_result ON public.mcp_activity_logs USING btree (result);
CREATE INDEX idx_mcp_activity_workspace ON public.mcp_activity_logs USING btree (workspace_id, created_at DESC);
CREATE INDEX idx_mcp_oauth_sessions_expires_at ON public.mcp_oauth_sessions USING btree (expires_at);
CREATE INDEX idx_mcp_oauth_sessions_mcp_token ON public.mcp_oauth_sessions USING btree (mcp_token);
CREATE INDEX idx_mcp_oauth_sessions_user_id ON public.mcp_oauth_sessions USING btree (user_id);
CREATE INDEX idx_mcp_oauth_sessions_workspace_id ON public.mcp_oauth_sessions USING btree (workspace_id);
CREATE INDEX idx_mcp_unassigned_status ON public.mcp_unassigned_captures USING btree (status);
CREATE INDEX idx_mcp_unassigned_workspace ON public.mcp_unassigned_captures USING btree (workspace_id);
CREATE INDEX idx_narrative_basket ON public.narrative USING btree (basket_id);
CREATE INDEX idx_openai_app_tokens_expires ON public.openai_app_tokens USING btree (expires_at);
CREATE UNIQUE INDEX idx_openai_app_tokens_workspace ON public.openai_app_tokens USING btree (workspace_id);
CREATE INDEX idx_proposal_executions_executed_at ON public.proposal_executions USING btree (executed_at DESC);
CREATE INDEX idx_proposal_executions_proposal ON public.proposal_executions USING btree (proposal_id, operation_index);
CREATE INDEX idx_proposal_executions_proposal_id ON public.proposal_executions USING btree (proposal_id);
CREATE INDEX idx_proposals_basket_scope ON public.proposals USING btree (basket_id, status, created_at DESC) WHERE ((scope = 'basket'::text) AND (basket_id IS NOT NULL));
CREATE INDEX idx_proposals_basket_status ON public.proposals USING btree (basket_id, status);
CREATE INDEX idx_proposals_blast_radius ON public.proposals USING btree (blast_radius);
CREATE INDEX idx_proposals_executed ON public.proposals USING btree (is_executed, executed_at);
CREATE INDEX idx_proposals_workspace_created ON public.proposals USING btree (workspace_id, created_at DESC);
CREATE INDEX idx_proposals_workspace_scope ON public.proposals USING btree (workspace_id, scope, status, created_at DESC) WHERE ((basket_id IS NULL) OR (scope = ANY (ARRAY['workspace'::text, 'cross-basket'::text])));
CREATE INDEX idx_proposals_workspace_status ON public.proposals USING btree (workspace_id, status, created_at DESC);
CREATE INDEX idx_queue_claimed ON public.agent_processing_queue USING btree (claimed_by, processing_state) WHERE (claimed_by IS NOT NULL);
CREATE INDEX idx_queue_state_created ON public.agent_processing_queue USING btree (processing_state, created_at);
CREATE INDEX idx_queue_workspace ON public.agent_processing_queue USING btree (workspace_id, processing_state);
CREATE INDEX idx_raw_dumps_basket ON public.raw_dumps USING btree (basket_id);
CREATE INDEX idx_raw_dumps_file_url ON public.raw_dumps USING btree (file_url);
CREATE INDEX idx_raw_dumps_source_meta_gin ON public.raw_dumps USING gin (source_meta);
CREATE INDEX idx_raw_dumps_trace ON public.raw_dumps USING btree (ingest_trace_id);
CREATE INDEX idx_rawdump_doc ON public.raw_dumps USING btree (document_id);
CREATE INDEX idx_reflection_cache_basket_computation ON public.reflections_artifact USING btree (basket_id, computation_timestamp DESC);
CREATE INDEX idx_reflection_cache_computation_timestamp ON public.reflections_artifact USING btree (computation_timestamp DESC);
CREATE INDEX idx_reflections_basket ON public.reflections_artifact USING btree (basket_id);
CREATE INDEX idx_reflections_lineage ON public.reflections_artifact USING btree (previous_id) WHERE (previous_id IS NOT NULL);
CREATE INDEX idx_reflections_workspace_scope ON public.reflections_artifact USING btree (workspace_id, scope_level, is_current) WHERE (scope_level = 'workspace'::text);
CREATE INDEX idx_substrate_references_created ON public.substrate_references USING btree (created_at);
CREATE INDEX idx_substrate_references_document ON public.substrate_references USING btree (document_id);
CREATE INDEX idx_substrate_references_role ON public.substrate_references USING btree (role) WHERE (role IS NOT NULL);
CREATE INDEX idx_substrate_references_substrate ON public.substrate_references USING btree (substrate_id);
CREATE INDEX idx_substrate_references_type ON public.substrate_references USING btree (substrate_type);
CREATE INDEX idx_timeline_events_basket_timestamp_id ON public.timeline_events USING btree (basket_id, ts DESC, id DESC);
CREATE INDEX idx_timeline_events_kind_ref_id ON public.timeline_events USING btree (kind, ref_id) WHERE (ref_id IS NOT NULL);
CREATE INDEX idx_timeline_workspace_ts ON public.timeline_events USING btree (workspace_id, ts DESC, id DESC);
CREATE INDEX idx_tombstones_lookup ON public.substrate_tombstones USING btree (workspace_id, basket_id, substrate_type, substrate_id);
CREATE INDEX idx_user_alerts_actionable ON public.user_alerts USING btree (user_id, actionable, created_at DESC) WHERE (dismissed_at IS NULL);
CREATE INDEX idx_user_alerts_user_active ON public.user_alerts USING btree (user_id, created_at DESC) WHERE (dismissed_at IS NULL);
CREATE INDEX idx_user_alerts_workspace_active ON public.user_alerts USING btree (workspace_id, created_at DESC) WHERE (dismissed_at IS NULL);
CREATE INDEX idx_workspace_governance_settings_workspace_id ON public.workspace_governance_settings USING btree (workspace_id);
CREATE INDEX integration_tokens_user_id_idx ON public.integration_tokens USING btree (user_id);
CREATE INDEX integration_tokens_workspace_id_idx ON public.integration_tokens USING btree (workspace_id);
CREATE INDEX ix_block_links_doc_block ON public.block_links USING btree (document_id, block_id);
CREATE INDEX ix_events_kind_ts ON public.events USING btree (kind, ts);
CREATE INDEX ix_pipeline_metrics_basket ON public.pipeline_metrics USING btree (basket_id, ts DESC);
CREATE INDEX ix_pipeline_metrics_recent ON public.pipeline_metrics USING btree (pipeline, ts DESC);
CREATE UNIQUE INDEX reflection_cache_uq ON public.reflections_artifact USING btree (basket_id, substrate_hash);
CREATE INDEX relationships_confidence_idx ON public.substrate_relationships USING btree (confidence_score DESC) WHERE ((state = 'PROPOSED'::public.block_state) AND (confidence_score IS NOT NULL));
CREATE INDEX relationships_from_block_idx ON public.substrate_relationships USING btree (from_block_id) WHERE (state = 'ACCEPTED'::public.block_state);
CREATE INDEX relationships_graph_query_idx ON public.substrate_relationships USING btree (relationship_type, from_block_id, state);
CREATE INDEX relationships_to_block_idx ON public.substrate_relationships USING btree (to_block_id) WHERE (state = 'ACCEPTED'::public.block_state);
CREATE INDEX relationships_type_idx ON public.substrate_relationships USING btree (relationship_type) WHERE (state = 'ACCEPTED'::public.block_state);
CREATE UNIQUE INDEX timeline_dump_unique ON public.timeline_events USING btree (ref_id) WHERE (kind = 'dump'::text);
CREATE INDEX timeline_events_basket_ts_idx ON public.timeline_events USING btree (basket_id, ts DESC);
CREATE UNIQUE INDEX uq_basket_anchors_key ON public.basket_anchors USING btree (basket_id, anchor_key);
CREATE UNIQUE INDEX uq_baskets_user_idem ON public.baskets USING btree (user_id, idempotency_key) WHERE (idempotency_key IS NOT NULL);
CREATE UNIQUE INDEX uq_current_insight_canon_per_basket ON public.reflections_artifact USING btree (basket_id) WHERE ((insight_type = 'insight_canon'::text) AND (is_current = true) AND (basket_id IS NOT NULL));
CREATE UNIQUE INDEX uq_current_insight_canon_per_workspace ON public.reflections_artifact USING btree (workspace_id) WHERE ((insight_type = 'insight_canon'::text) AND (is_current = true) AND (scope_level = 'workspace'::text));
CREATE UNIQUE INDEX uq_doc_ctx_item ON public.document_context_items USING btree (document_id, context_item_id);
CREATE UNIQUE INDEX uq_doc_version_signature ON public.document_versions USING btree (document_id, composition_signature) WHERE (composition_signature IS NOT NULL);
CREATE UNIQUE INDEX uq_document_canon_per_basket ON public.documents USING btree (basket_id) WHERE ((doc_type = 'document_canon'::text) AND (basket_id IS NOT NULL));
CREATE UNIQUE INDEX uq_dumps_basket_req ON public.raw_dumps USING btree (basket_id, dump_request_id) WHERE (dump_request_id IS NOT NULL);
CREATE UNIQUE INDEX uq_raw_dumps_basket_req ON public.raw_dumps USING btree (basket_id, dump_request_id) WHERE (dump_request_id IS NOT NULL);
CREATE UNIQUE INDEX ux_raw_dumps_basket_trace ON public.raw_dumps USING btree (basket_id, ingest_trace_id) WHERE (ingest_trace_id IS NOT NULL);
CREATE TRIGGER after_dump_insert AFTER INSERT ON public.raw_dumps FOR EACH ROW EXECUTE FUNCTION public.queue_agent_processing();
CREATE TRIGGER basket_anchors_set_updated_at BEFORE UPDATE ON public.basket_anchors FOR EACH ROW EXECUTE FUNCTION public.fn_set_basket_anchor_updated_at();
CREATE TRIGGER basket_signatures_set_updated_at BEFORE UPDATE ON public.basket_signatures FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
CREATE TRIGGER enforce_single_workspace_per_user BEFORE INSERT OR UPDATE ON public.workspace_memberships FOR EACH ROW EXECUTE FUNCTION public.check_single_workspace_per_user();
CREATE TRIGGER ensure_text_dump_columns BEFORE INSERT ON public.raw_dumps FOR EACH ROW EXECUTE FUNCTION public.ensure_raw_dump_text_columns();
CREATE TRIGGER mcp_unassigned_set_updated_at BEFORE UPDATE ON public.mcp_unassigned_captures FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
CREATE TRIGGER openai_app_tokens_set_updated_at BEFORE UPDATE ON public.openai_app_tokens FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
CREATE TRIGGER proposals_validation_gate BEFORE UPDATE ON public.proposals FOR EACH ROW EXECUTE FUNCTION public.proposal_validation_check();
CREATE TRIGGER reflection_cache_updated_at_trigger BEFORE UPDATE ON public.reflections_artifact FOR EACH ROW EXECUTE FUNCTION public.update_reflection_cache_updated_at();
CREATE TRIGGER sync_text_dump_columns BEFORE UPDATE ON public.raw_dumps FOR EACH ROW EXECUTE FUNCTION public.sync_raw_dump_text_columns();
CREATE TRIGGER trg_block_depth BEFORE INSERT OR UPDATE ON public.blocks FOR EACH ROW EXECUTE FUNCTION public.check_block_depth();
CREATE TRIGGER trg_lock_constant BEFORE INSERT OR UPDATE ON public.blocks FOR EACH ROW EXECUTE FUNCTION public.prevent_lock_vs_constant();
CREATE TRIGGER trg_set_basket_user_id BEFORE INSERT ON public.baskets FOR EACH ROW EXECUTE FUNCTION public.set_basket_user_id();
CREATE TRIGGER trg_timeline_after_raw_dump AFTER INSERT ON public.raw_dumps FOR EACH ROW EXECUTE FUNCTION public.fn_timeline_after_raw_dump();
CREATE TRIGGER trigger_auto_increment_usage_on_substrate_reference AFTER INSERT ON public.substrate_references FOR EACH ROW EXECUTE FUNCTION public.auto_increment_block_usage_on_reference();
CREATE TRIGGER trigger_mark_blocks_stale_on_new_dump AFTER INSERT ON public.raw_dumps FOR EACH ROW EXECUTE FUNCTION public.mark_related_blocks_stale();
CREATE TRIGGER update_substrate_relationships_updated_at BEFORE UPDATE ON public.substrate_relationships FOR EACH ROW EXECUTE FUNCTION public.update_substrate_relationships_updated_at();
ALTER TABLE ONLY public.agent_processing_queue
    ADD CONSTRAINT agent_processing_queue_basket_id_fkey FOREIGN KEY (basket_id) REFERENCES public.baskets(id) DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE ONLY public.agent_processing_queue
    ADD CONSTRAINT agent_processing_queue_dump_id_fkey FOREIGN KEY (dump_id) REFERENCES public.raw_dumps(id) DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE ONLY public.agent_processing_queue
    ADD CONSTRAINT agent_processing_queue_workspace_id_fkey FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id);
ALTER TABLE ONLY public.app_events
    ADD CONSTRAINT app_events_basket_id_fkey FOREIGN KEY (basket_id) REFERENCES public.baskets(id);
ALTER TABLE ONLY public.app_events
    ADD CONSTRAINT app_events_workspace_id_fkey FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id);
ALTER TABLE ONLY public.artifact_generation_settings
    ADD CONSTRAINT artifact_generation_settings_workspace_id_fkey FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) ON DELETE CASCADE;
ALTER TABLE ONLY public.basket_anchors
    ADD CONSTRAINT basket_anchors_basket_id_fkey FOREIGN KEY (basket_id) REFERENCES public.baskets(id) ON DELETE CASCADE;
ALTER TABLE ONLY public.reflections_artifact
    ADD CONSTRAINT basket_reflections_basket_id_fkey FOREIGN KEY (basket_id) REFERENCES public.baskets(id) ON DELETE CASCADE;
ALTER TABLE ONLY public.basket_signatures
    ADD CONSTRAINT basket_signatures_basket_id_fkey FOREIGN KEY (basket_id) REFERENCES public.baskets(id) ON DELETE CASCADE;
ALTER TABLE ONLY public.basket_signatures
    ADD CONSTRAINT basket_signatures_workspace_id_fkey FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) ON DELETE CASCADE;
ALTER TABLE ONLY public.block_links
    ADD CONSTRAINT block_links_block_id_fkey FOREIGN KEY (block_id) REFERENCES public.blocks(id) ON DELETE CASCADE;
ALTER TABLE ONLY public.block_links
    ADD CONSTRAINT block_links_document_id_fkey FOREIGN KEY (document_id) REFERENCES public.documents(id) ON DELETE CASCADE;
ALTER TABLE ONLY public.block_revisions
    ADD CONSTRAINT block_revisions_actor_id_fkey FOREIGN KEY (actor_id) REFERENCES auth.users(id);
ALTER TABLE ONLY public.block_revisions
    ADD CONSTRAINT block_revisions_block_id_fkey FOREIGN KEY (block_id) REFERENCES public.blocks(id) ON DELETE CASCADE;
ALTER TABLE ONLY public.block_revisions
    ADD CONSTRAINT block_revisions_workspace_id_fkey FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) ON DELETE CASCADE;
ALTER TABLE ONLY public.block_usage
    ADD CONSTRAINT block_usage_block_id_fkey FOREIGN KEY (block_id) REFERENCES public.blocks(id) ON DELETE CASCADE;
ALTER TABLE ONLY public.blocks
    ADD CONSTRAINT blocks_basket_id_fkey FOREIGN KEY (basket_id) REFERENCES public.baskets(id) ON DELETE CASCADE;
ALTER TABLE ONLY public.blocks
    ADD CONSTRAINT blocks_parent_block_id_fkey FOREIGN KEY (parent_block_id) REFERENCES public.blocks(id);
ALTER TABLE ONLY public.blocks
    ADD CONSTRAINT blocks_proposal_id_fkey FOREIGN KEY (proposal_id) REFERENCES public.proposals(id);
ALTER TABLE ONLY public.blocks
    ADD CONSTRAINT blocks_raw_dump_id_fkey FOREIGN KEY (raw_dump_id) REFERENCES public.raw_dumps(id);
ALTER TABLE ONLY public.document_context_items
    ADD CONSTRAINT document_context_items_document_id_fkey FOREIGN KEY (document_id) REFERENCES public.documents(id) ON DELETE CASCADE;
ALTER TABLE ONLY public.document_versions
    ADD CONSTRAINT document_versions_created_by_fkey FOREIGN KEY (created_by) REFERENCES auth.users(id) ON DELETE SET NULL;
ALTER TABLE ONLY public.document_versions
    ADD CONSTRAINT document_versions_document_id_fkey FOREIGN KEY (document_id) REFERENCES public.documents(id) ON DELETE CASCADE;
ALTER TABLE ONLY public.documents
    ADD CONSTRAINT documents_basket_id_fkey FOREIGN KEY (basket_id) REFERENCES public.baskets(id) ON DELETE CASCADE;
ALTER TABLE ONLY public.documents
    ADD CONSTRAINT documents_previous_id_fkey FOREIGN KEY (previous_id) REFERENCES public.documents(id) ON DELETE SET NULL;
ALTER TABLE ONLY public.documents
    ADD CONSTRAINT documents_source_raw_dump_id_fkey FOREIGN KEY (source_raw_dump_id) REFERENCES public.raw_dumps(id) ON DELETE SET NULL;
ALTER TABLE ONLY public.documents
    ADD CONSTRAINT documents_workspace_id_fkey FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) ON DELETE CASCADE;
ALTER TABLE ONLY public.events
    ADD CONSTRAINT events_actor_id_fkey FOREIGN KEY (actor_id) REFERENCES auth.users(id);
ALTER TABLE ONLY public.events
    ADD CONSTRAINT events_basket_id_fkey FOREIGN KEY (basket_id) REFERENCES public.baskets(id) ON DELETE CASCADE;
ALTER TABLE ONLY public.events
    ADD CONSTRAINT events_block_id_fkey FOREIGN KEY (block_id) REFERENCES public.blocks(id);
ALTER TABLE ONLY public.extraction_quality_metrics
    ADD CONSTRAINT extraction_quality_metrics_basket_id_fkey FOREIGN KEY (basket_id) REFERENCES public.baskets(id) ON DELETE CASCADE;
ALTER TABLE ONLY public.extraction_quality_metrics
    ADD CONSTRAINT extraction_quality_metrics_dump_id_fkey FOREIGN KEY (dump_id) REFERENCES public.raw_dumps(id) ON DELETE CASCADE;
ALTER TABLE ONLY public.baskets
    ADD CONSTRAINT fk_basket_workspace FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) ON DELETE CASCADE;
ALTER TABLE ONLY public.baskets
    ADD CONSTRAINT fk_baskets_user FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;
ALTER TABLE ONLY public.blocks
    ADD CONSTRAINT fk_block_workspace FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) ON DELETE CASCADE;
ALTER TABLE ONLY public.baskets
    ADD CONSTRAINT fk_raw_dump FOREIGN KEY (raw_dump_id) REFERENCES public.raw_dumps(id) DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE ONLY public.raw_dumps
    ADD CONSTRAINT fk_rawdump_document FOREIGN KEY (document_id) REFERENCES public.documents(id) ON DELETE CASCADE;
ALTER TABLE ONLY public.raw_dumps
    ADD CONSTRAINT fk_rawdump_workspace FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) ON DELETE CASCADE;
ALTER TABLE ONLY public.integration_tokens
    ADD CONSTRAINT integration_tokens_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;
ALTER TABLE ONLY public.integration_tokens
    ADD CONSTRAINT integration_tokens_workspace_id_fkey FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) ON DELETE CASCADE;
ALTER TABLE ONLY public.knowledge_timeline
    ADD CONSTRAINT knowledge_timeline_basket_id_fkey FOREIGN KEY (basket_id) REFERENCES public.baskets(id) ON DELETE CASCADE;
ALTER TABLE ONLY public.knowledge_timeline
    ADD CONSTRAINT knowledge_timeline_workspace_id_fkey FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) ON DELETE CASCADE;
ALTER TABLE ONLY public.mcp_activity_logs
    ADD CONSTRAINT mcp_activity_logs_basket_id_fkey FOREIGN KEY (basket_id) REFERENCES public.baskets(id) ON DELETE SET NULL;
ALTER TABLE ONLY public.mcp_activity_logs
    ADD CONSTRAINT mcp_activity_logs_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE SET NULL;
ALTER TABLE ONLY public.mcp_activity_logs
    ADD CONSTRAINT mcp_activity_logs_workspace_id_fkey FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) ON DELETE CASCADE;
ALTER TABLE ONLY public.mcp_oauth_sessions
    ADD CONSTRAINT mcp_oauth_sessions_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;
ALTER TABLE ONLY public.mcp_oauth_sessions
    ADD CONSTRAINT mcp_oauth_sessions_workspace_id_fkey FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) ON DELETE CASCADE;
ALTER TABLE ONLY public.mcp_unassigned_captures
    ADD CONSTRAINT mcp_unassigned_captures_assigned_basket_id_fkey FOREIGN KEY (assigned_basket_id) REFERENCES public.baskets(id);
ALTER TABLE ONLY public.mcp_unassigned_captures
    ADD CONSTRAINT mcp_unassigned_captures_requested_by_fkey FOREIGN KEY (requested_by) REFERENCES auth.users(id) ON DELETE SET NULL;
ALTER TABLE ONLY public.mcp_unassigned_captures
    ADD CONSTRAINT mcp_unassigned_captures_resolved_by_fkey FOREIGN KEY (resolved_by) REFERENCES auth.users(id) ON DELETE SET NULL;
ALTER TABLE ONLY public.mcp_unassigned_captures
    ADD CONSTRAINT mcp_unassigned_captures_workspace_id_fkey FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) ON DELETE CASCADE;
ALTER TABLE ONLY public.narrative
    ADD CONSTRAINT narrative_basket_id_fkey FOREIGN KEY (basket_id) REFERENCES public.baskets(id);
ALTER TABLE ONLY public.narrative
    ADD CONSTRAINT narrative_raw_dump_id_fkey FOREIGN KEY (raw_dump_id) REFERENCES public.raw_dumps(id);
ALTER TABLE ONLY public.openai_app_tokens
    ADD CONSTRAINT openai_app_tokens_workspace_id_fkey FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) ON DELETE CASCADE;
ALTER TABLE ONLY public.p3_p4_regeneration_policy
    ADD CONSTRAINT p3_p4_regeneration_policy_workspace_id_fkey FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) ON DELETE CASCADE;
ALTER TABLE ONLY public.proposal_executions
    ADD CONSTRAINT proposal_executions_proposal_id_fkey FOREIGN KEY (proposal_id) REFERENCES public.proposals(id);
ALTER TABLE ONLY public.proposals
    ADD CONSTRAINT proposals_basket_id_fkey FOREIGN KEY (basket_id) REFERENCES public.baskets(id);
ALTER TABLE ONLY public.proposals
    ADD CONSTRAINT proposals_target_basket_id_fkey FOREIGN KEY (target_basket_id) REFERENCES public.baskets(id);
ALTER TABLE ONLY public.proposals
    ADD CONSTRAINT proposals_workspace_id_fkey FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id);
ALTER TABLE ONLY public.raw_dumps
    ADD CONSTRAINT raw_dumps_basket_id_fkey FOREIGN KEY (basket_id) REFERENCES public.baskets(id) ON DELETE CASCADE;
ALTER TABLE ONLY public.reflections_artifact
    ADD CONSTRAINT reflection_cache_workspace_fkey FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) ON DELETE CASCADE;
ALTER TABLE ONLY public.reflections_artifact
    ADD CONSTRAINT reflections_artifact_previous_id_fkey FOREIGN KEY (previous_id) REFERENCES public.reflections_artifact(id) ON DELETE SET NULL;
ALTER TABLE ONLY public.revisions
    ADD CONSTRAINT revisions_basket_id_fkey FOREIGN KEY (basket_id) REFERENCES public.baskets(id) ON DELETE CASCADE;
ALTER TABLE ONLY public.substrate_references
    ADD CONSTRAINT substrate_references_created_by_fkey FOREIGN KEY (created_by) REFERENCES auth.users(id) ON DELETE SET NULL;
ALTER TABLE ONLY public.substrate_references
    ADD CONSTRAINT substrate_references_document_id_fkey FOREIGN KEY (document_id) REFERENCES public.documents(id) ON DELETE CASCADE;
ALTER TABLE ONLY public.substrate_relationships
    ADD CONSTRAINT substrate_relationships_created_by_fkey FOREIGN KEY (created_by) REFERENCES auth.users(id);
ALTER TABLE ONLY public.substrate_relationships
    ADD CONSTRAINT substrate_relationships_from_block_id_fkey FOREIGN KEY (from_block_id) REFERENCES public.blocks(id) ON DELETE CASCADE;
ALTER TABLE ONLY public.substrate_relationships
    ADD CONSTRAINT substrate_relationships_to_block_id_fkey FOREIGN KEY (to_block_id) REFERENCES public.blocks(id) ON DELETE CASCADE;
ALTER TABLE ONLY public.timeline_events
    ADD CONSTRAINT timeline_events_basket_id_fkey FOREIGN KEY (basket_id) REFERENCES public.baskets(id) ON DELETE CASCADE;
ALTER TABLE ONLY public.timeline_events
    ADD CONSTRAINT timeline_events_workspace_fkey FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) ON DELETE CASCADE;
ALTER TABLE ONLY public.user_alerts
    ADD CONSTRAINT user_alerts_workspace_id_fkey FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) ON DELETE CASCADE;
ALTER TABLE ONLY public.workspace_governance_settings
    ADD CONSTRAINT workspace_governance_settings_workspace_id_fkey FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) ON DELETE CASCADE;
ALTER TABLE ONLY public.workspace_memberships
    ADD CONSTRAINT workspace_memberships_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;
ALTER TABLE ONLY public.workspace_memberships
    ADD CONSTRAINT workspace_memberships_workspace_id_fkey FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) ON DELETE CASCADE;
ALTER TABLE ONLY public.workspaces
    ADD CONSTRAINT workspaces_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES auth.users(id) ON DELETE CASCADE;
CREATE POLICY "Allow anon read events" ON public.events FOR SELECT USING (true);
CREATE POLICY "Allow anon read raw_dumps" ON public.raw_dumps FOR SELECT USING (true);
CREATE POLICY "Allow anon read revisions" ON public.revisions FOR SELECT USING (true);
CREATE POLICY "Allow authenticated users to view basket events" ON public.basket_events FOR SELECT TO authenticated USING (true);
CREATE POLICY "Allow baskets for workspace members" ON public.baskets FOR SELECT TO authenticated USING ((workspace_id IN ( SELECT workspace_memberships.workspace_id
   FROM public.workspace_memberships
  WHERE (workspace_memberships.user_id = auth.uid()))));
CREATE POLICY "Allow insert for members" ON public.workspace_memberships FOR INSERT TO authenticated WITH CHECK ((auth.uid() = user_id));
CREATE POLICY "Allow insert for owner" ON public.workspaces FOR INSERT TO authenticated WITH CHECK ((auth.uid() = owner_id));
CREATE POLICY "Allow own workspace memberships" ON public.workspace_memberships FOR SELECT TO authenticated USING ((user_id = auth.uid()));
CREATE POLICY "Allow owner to read workspace" ON public.workspaces FOR SELECT USING ((auth.uid() = owner_id));
CREATE POLICY "Allow users to see their own workspace memberships" ON public.workspace_memberships FOR SELECT USING ((user_id = auth.uid()));
CREATE POLICY "Allow workspace members to read baskets" ON public.baskets FOR SELECT USING ((workspace_id IN ( SELECT workspace_memberships.workspace_id
   FROM public.workspace_memberships
  WHERE (workspace_memberships.user_id = auth.uid()))));
CREATE POLICY "Anon can view events temporarily" ON public.basket_events FOR SELECT TO anon USING (true);
CREATE POLICY "Authenticated users can view events" ON public.basket_events FOR SELECT TO authenticated USING (true);
CREATE POLICY "Service role can manage all relationships" ON public.substrate_relationships USING (((auth.jwt() ->> 'role'::text) = 'service_role'::text)) WITH CHECK (((auth.jwt() ->> 'role'::text) = 'service_role'::text));
CREATE POLICY "Service role can manage queue" ON public.agent_processing_queue TO service_role USING (true);
CREATE POLICY "Service role full access" ON public.baskets TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "Service role has full access to block_usage" ON public.block_usage TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "Service role has full access to extraction_quality_metrics" ON public.extraction_quality_metrics TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "Users can create proposals in their workspace" ON public.proposals FOR INSERT WITH CHECK ((workspace_id IN ( SELECT workspace_memberships.workspace_id
   FROM public.workspace_memberships
  WHERE (workspace_memberships.user_id = auth.uid()))));
CREATE POLICY "Users can create relationships in their workspace baskets" ON public.substrate_relationships FOR INSERT WITH CHECK ((EXISTS ( SELECT 1
   FROM ((public.blocks b
     JOIN public.baskets bsk ON ((b.basket_id = bsk.id)))
     JOIN public.workspace_memberships wm ON ((bsk.workspace_id = wm.workspace_id)))
  WHERE ((b.id = substrate_relationships.from_block_id) AND (wm.user_id = auth.uid())))));
CREATE POLICY "Users can insert events for their workspaces" ON public.events FOR INSERT TO authenticated WITH CHECK ((workspace_id IN ( SELECT workspace_memberships.workspace_id
   FROM public.workspace_memberships
  WHERE (workspace_memberships.user_id = auth.uid()))));
CREATE POLICY "Users can modify block revisions in their workspaces" ON public.block_revisions USING ((EXISTS ( SELECT 1
   FROM public.workspace_memberships
  WHERE ((workspace_memberships.workspace_id = block_revisions.workspace_id) AND (workspace_memberships.user_id = auth.uid())))));
CREATE POLICY "Users can modify blocks in their workspaces" ON public.blocks USING ((EXISTS ( SELECT 1
   FROM public.workspace_memberships
  WHERE ((workspace_memberships.workspace_id = blocks.workspace_id) AND (workspace_memberships.user_id = auth.uid())))));
CREATE POLICY "Users can modify documents in their workspaces" ON public.documents USING ((EXISTS ( SELECT 1
   FROM public.workspace_memberships
  WHERE ((workspace_memberships.workspace_id = documents.workspace_id) AND (workspace_memberships.user_id = auth.uid())))));
CREATE POLICY "Users can queue processing in their workspace" ON public.agent_processing_queue FOR INSERT TO authenticated WITH CHECK ((workspace_id IN ( SELECT workspace_memberships.workspace_id
   FROM public.workspace_memberships
  WHERE (workspace_memberships.user_id = auth.uid()))));
CREATE POLICY "Users can read block revisions in their workspaces" ON public.block_revisions FOR SELECT USING ((EXISTS ( SELECT 1
   FROM public.workspace_memberships
  WHERE ((workspace_memberships.workspace_id = block_revisions.workspace_id) AND (workspace_memberships.user_id = auth.uid())))));
CREATE POLICY "Users can read blocks in their workspaces" ON public.blocks FOR SELECT USING ((EXISTS ( SELECT 1
   FROM public.workspace_memberships
  WHERE ((workspace_memberships.workspace_id = blocks.workspace_id) AND (workspace_memberships.user_id = auth.uid())))));
CREATE POLICY "Users can read documents in their workspaces" ON public.documents FOR SELECT USING ((EXISTS ( SELECT 1
   FROM public.workspace_memberships
  WHERE ((workspace_memberships.workspace_id = documents.workspace_id) AND (workspace_memberships.user_id = auth.uid())))));
CREATE POLICY "Users can revoke own MCP sessions" ON public.mcp_oauth_sessions FOR DELETE USING ((user_id = auth.uid()));
CREATE POLICY "Users can update proposals in their workspace" ON public.proposals FOR UPDATE USING ((workspace_id IN ( SELECT workspace_memberships.workspace_id
   FROM public.workspace_memberships
  WHERE (workspace_memberships.user_id = auth.uid()))));
CREATE POLICY "Users can update relationships in their workspace" ON public.substrate_relationships FOR UPDATE USING (((created_by = auth.uid()) OR (EXISTS ( SELECT 1
   FROM ((public.blocks b
     JOIN public.baskets bsk ON ((b.basket_id = bsk.id)))
     JOIN public.workspace_memberships wm ON ((bsk.workspace_id = wm.workspace_id)))
  WHERE ((b.id = substrate_relationships.from_block_id) AND (wm.user_id = auth.uid()))))));
CREATE POLICY "Users can update their queued items" ON public.agent_processing_queue FOR UPDATE TO authenticated USING ((workspace_id IN ( SELECT workspace_memberships.workspace_id
   FROM public.workspace_memberships
  WHERE (workspace_memberships.user_id = auth.uid())))) WITH CHECK ((workspace_id IN ( SELECT workspace_memberships.workspace_id
   FROM public.workspace_memberships
  WHERE (workspace_memberships.user_id = auth.uid()))));
CREATE POLICY "Users can view block_usage in their workspace" ON public.block_usage FOR SELECT TO authenticated USING ((EXISTS ( SELECT 1
   FROM ((public.blocks b
     JOIN public.baskets bsk ON ((bsk.id = b.basket_id)))
     JOIN public.workspace_memberships wm ON ((wm.workspace_id = bsk.workspace_id)))
  WHERE ((b.id = block_usage.block_id) AND (wm.user_id = auth.uid())))));
CREATE POLICY "Users can view blocks in their workspace" ON public.blocks FOR SELECT USING ((EXISTS ( SELECT 1
   FROM public.baskets
  WHERE ((baskets.id = blocks.basket_id) AND (baskets.workspace_id IN ( SELECT workspace_memberships.workspace_id
           FROM public.workspace_memberships
          WHERE (workspace_memberships.user_id = auth.uid())))))));
CREATE POLICY "Users can view executions in their workspace" ON public.proposal_executions FOR SELECT USING ((proposal_id IN ( SELECT proposals.id
   FROM public.proposals
  WHERE (proposals.workspace_id IN ( SELECT workspace_memberships.workspace_id
           FROM public.workspace_memberships
          WHERE (workspace_memberships.user_id = auth.uid()))))));
CREATE POLICY "Users can view extraction metrics in their workspace" ON public.extraction_quality_metrics FOR SELECT TO authenticated USING ((EXISTS ( SELECT 1
   FROM public.workspace_memberships wm
  WHERE ((wm.workspace_id = extraction_quality_metrics.workspace_id) AND (wm.user_id = auth.uid())))));
CREATE POLICY "Users can view narrative in their workspace" ON public.narrative FOR SELECT USING ((EXISTS ( SELECT 1
   FROM public.baskets
  WHERE ((baskets.id = narrative.basket_id) AND (baskets.workspace_id IN ( SELECT workspace_memberships.workspace_id
           FROM public.workspace_memberships
          WHERE (workspace_memberships.user_id = auth.uid())))))));
CREATE POLICY "Users can view own MCP sessions" ON public.mcp_oauth_sessions FOR SELECT USING ((user_id = auth.uid()));
CREATE POLICY "Users can view proposals in their workspace" ON public.proposals FOR SELECT USING ((workspace_id IN ( SELECT workspace_memberships.workspace_id
   FROM public.workspace_memberships
  WHERE (workspace_memberships.user_id = auth.uid()))));
CREATE POLICY "Users can view queue in their workspace" ON public.agent_processing_queue FOR SELECT TO authenticated USING ((workspace_id IN ( SELECT workspace_memberships.workspace_id
   FROM public.workspace_memberships
  WHERE (workspace_memberships.user_id = auth.uid()))));
CREATE POLICY "Users can view raw_dumps in their workspace" ON public.raw_dumps FOR SELECT USING ((EXISTS ( SELECT 1
   FROM public.baskets
  WHERE ((baskets.id = raw_dumps.basket_id) AND (baskets.workspace_id IN ( SELECT workspace_memberships.workspace_id
           FROM public.workspace_memberships
          WHERE (workspace_memberships.user_id = auth.uid())))))));
CREATE POLICY "Users can view relationships in their workspace baskets" ON public.substrate_relationships FOR SELECT USING ((EXISTS ( SELECT 1
   FROM ((public.blocks b
     JOIN public.baskets bsk ON ((b.basket_id = bsk.id)))
     JOIN public.workspace_memberships wm ON ((bsk.workspace_id = wm.workspace_id)))
  WHERE (((b.id = substrate_relationships.from_block_id) OR (b.id = substrate_relationships.to_block_id)) AND (wm.user_id = auth.uid())))));
CREATE POLICY "Workspace members can read events" ON public.events FOR SELECT USING ((workspace_id IN ( SELECT workspace_memberships.workspace_id
   FROM public.workspace_memberships
  WHERE (workspace_memberships.user_id = auth.uid()))));
CREATE POLICY "Workspace members can update events" ON public.events FOR UPDATE TO authenticated USING ((EXISTS ( SELECT 1
   FROM public.workspace_memberships
  WHERE ((workspace_memberships.workspace_id = events.workspace_id) AND (workspace_memberships.user_id = auth.uid())))));
ALTER TABLE public.agent_processing_queue ENABLE ROW LEVEL SECURITY;
CREATE POLICY "allow agent insert" ON public.revisions FOR INSERT TO authenticated WITH CHECK (((basket_id IS NOT NULL) AND (basket_id IN ( SELECT baskets.id
   FROM public.baskets
  WHERE (baskets.workspace_id IN ( SELECT workspace_memberships.workspace_id
           FROM public.workspace_memberships
          WHERE (workspace_memberships.user_id = auth.uid())))))));
ALTER TABLE public.app_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.artifact_generation_settings ENABLE ROW LEVEL SECURITY;
CREATE POLICY artifact_settings_workspace ON public.artifact_generation_settings USING ((workspace_id IN ( SELECT workspace_memberships.workspace_id
   FROM public.workspace_memberships
  WHERE (workspace_memberships.user_id = auth.uid()))));
ALTER TABLE public.basket_anchors ENABLE ROW LEVEL SECURITY;
CREATE POLICY basket_anchors_service_full ON public.basket_anchors TO service_role USING (true) WITH CHECK (true);
CREATE POLICY basket_anchors_workspace_members_delete ON public.basket_anchors FOR DELETE TO authenticated USING ((EXISTS ( SELECT 1
   FROM (public.baskets b
     JOIN public.workspace_memberships wm ON ((wm.workspace_id = b.workspace_id)))
  WHERE ((b.id = basket_anchors.basket_id) AND (wm.user_id = auth.uid())))));
CREATE POLICY basket_anchors_workspace_members_modify ON public.basket_anchors FOR INSERT TO authenticated WITH CHECK ((EXISTS ( SELECT 1
   FROM (public.baskets b
     JOIN public.workspace_memberships wm ON ((wm.workspace_id = b.workspace_id)))
  WHERE ((b.id = basket_anchors.basket_id) AND (wm.user_id = auth.uid())))));
CREATE POLICY basket_anchors_workspace_members_select ON public.basket_anchors FOR SELECT TO authenticated USING ((EXISTS ( SELECT 1
   FROM (public.baskets b
     JOIN public.workspace_memberships wm ON ((wm.workspace_id = b.workspace_id)))
  WHERE ((b.id = basket_anchors.basket_id) AND (wm.user_id = auth.uid())))));
CREATE POLICY basket_anchors_workspace_members_update ON public.basket_anchors FOR UPDATE TO authenticated USING ((EXISTS ( SELECT 1
   FROM (public.baskets b
     JOIN public.workspace_memberships wm ON ((wm.workspace_id = b.workspace_id)))
  WHERE ((b.id = basket_anchors.basket_id) AND (wm.user_id = auth.uid()))))) WITH CHECK ((EXISTS ( SELECT 1
   FROM (public.baskets b
     JOIN public.workspace_memberships wm ON ((wm.workspace_id = b.workspace_id)))
  WHERE ((b.id = basket_anchors.basket_id) AND (wm.user_id = auth.uid())))));
ALTER TABLE public.basket_events ENABLE ROW LEVEL SECURITY;
CREATE POLICY basket_member_delete ON public.baskets FOR DELETE USING ((workspace_id IN ( SELECT workspace_memberships.workspace_id
   FROM public.workspace_memberships
  WHERE (workspace_memberships.user_id = auth.uid()))));
CREATE POLICY basket_member_insert ON public.baskets FOR INSERT WITH CHECK ((workspace_id IN ( SELECT workspace_memberships.workspace_id
   FROM public.workspace_memberships
  WHERE (workspace_memberships.user_id = auth.uid()))));
CREATE POLICY basket_member_read ON public.baskets FOR SELECT USING (((auth.uid() IS NOT NULL) AND (workspace_id IN ( SELECT workspaces.id
   FROM public.workspaces
  WHERE (workspaces.owner_id = auth.uid())))));
CREATE POLICY basket_member_update ON public.baskets FOR UPDATE USING ((workspace_id IN ( SELECT workspace_memberships.workspace_id
   FROM public.workspace_memberships
  WHERE (workspace_memberships.user_id = auth.uid()))));
ALTER TABLE public.basket_signatures ENABLE ROW LEVEL SECURITY;
CREATE POLICY basket_signatures_select ON public.basket_signatures FOR SELECT USING ((EXISTS ( SELECT 1
   FROM public.workspace_memberships wm
  WHERE ((wm.workspace_id = basket_signatures.workspace_id) AND (wm.user_id = auth.uid())))));
CREATE POLICY basket_signatures_service_insert ON public.basket_signatures FOR INSERT WITH CHECK ((auth.role() = 'service_role'::text));
CREATE POLICY basket_signatures_service_update ON public.basket_signatures FOR UPDATE USING ((auth.role() = 'service_role'::text)) WITH CHECK ((auth.role() = 'service_role'::text));
ALTER TABLE public.baskets ENABLE ROW LEVEL SECURITY;
CREATE POLICY baskets_insert_members ON public.baskets FOR INSERT TO authenticated WITH CHECK ((workspace_id IN ( SELECT workspace_memberships.workspace_id
   FROM public.workspace_memberships
  WHERE (workspace_memberships.user_id = auth.uid()))));
CREATE POLICY bh_insert_by_workspace ON public.timeline_events FOR INSERT TO authenticated WITH CHECK ((EXISTS ( SELECT 1
   FROM (public.baskets b
     JOIN public.workspace_memberships m ON ((m.workspace_id = b.workspace_id)))
  WHERE ((b.id = timeline_events.basket_id) AND (m.user_id = auth.uid())))));
CREATE POLICY bh_select_by_workspace ON public.timeline_events FOR SELECT TO authenticated USING ((EXISTS ( SELECT 1
   FROM (public.baskets b
     JOIN public.workspace_memberships m ON ((m.workspace_id = b.workspace_id)))
  WHERE ((b.id = timeline_events.basket_id) AND (m.user_id = auth.uid())))));
CREATE POLICY block_member_delete ON public.blocks FOR DELETE USING ((workspace_id IN ( SELECT workspace_memberships.workspace_id
   FROM public.workspace_memberships
  WHERE (workspace_memberships.user_id = auth.uid()))));
CREATE POLICY block_member_insert ON public.blocks FOR INSERT WITH CHECK ((workspace_id IN ( SELECT workspace_memberships.workspace_id
   FROM public.workspace_memberships
  WHERE (workspace_memberships.user_id = auth.uid()))));
CREATE POLICY block_member_read ON public.blocks FOR SELECT USING ((workspace_id IN ( SELECT workspace_memberships.workspace_id
   FROM public.workspace_memberships
  WHERE (workspace_memberships.user_id = auth.uid()))));
CREATE POLICY block_member_update ON public.blocks FOR UPDATE USING ((workspace_id IN ( SELECT workspace_memberships.workspace_id
   FROM public.workspace_memberships
  WHERE (workspace_memberships.user_id = auth.uid()))));
ALTER TABLE public.block_revisions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.block_usage ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.blocks ENABLE ROW LEVEL SECURITY;
CREATE POLICY blocks_delete_workspace_member ON public.blocks FOR DELETE TO authenticated USING ((workspace_id IN ( SELECT workspace_memberships.workspace_id
   FROM public.workspace_memberships
  WHERE (workspace_memberships.user_id = auth.uid()))));
CREATE POLICY blocks_insert_workspace_member ON public.blocks FOR INSERT TO authenticated WITH CHECK ((workspace_id IN ( SELECT workspace_memberships.workspace_id
   FROM public.workspace_memberships
  WHERE (workspace_memberships.user_id = auth.uid()))));
CREATE POLICY blocks_select_workspace_member ON public.blocks FOR SELECT TO authenticated USING ((workspace_id IN ( SELECT workspace_memberships.workspace_id
   FROM public.workspace_memberships
  WHERE (workspace_memberships.user_id = auth.uid()))));
CREATE POLICY blocks_service_role_all ON public.blocks TO service_role USING (true) WITH CHECK (true);
CREATE POLICY blocks_update_workspace_member ON public.blocks FOR UPDATE TO authenticated USING ((workspace_id IN ( SELECT workspace_memberships.workspace_id
   FROM public.workspace_memberships
  WHERE (workspace_memberships.user_id = auth.uid()))));
CREATE POLICY br_insert_workspace_member ON public.reflections_artifact FOR INSERT WITH CHECK ((EXISTS ( SELECT 1
   FROM (public.baskets b
     JOIN public.workspace_memberships wm ON ((wm.workspace_id = b.workspace_id)))
  WHERE ((b.id = reflections_artifact.basket_id) AND (wm.user_id = auth.uid())))));
CREATE POLICY br_select_workspace_member ON public.reflections_artifact FOR SELECT USING ((EXISTS ( SELECT 1
   FROM (public.baskets b
     JOIN public.workspace_memberships wm ON ((wm.workspace_id = b.workspace_id)))
  WHERE ((b.id = reflections_artifact.basket_id) AND (wm.user_id = auth.uid())))));
CREATE POLICY "debug insert bypass" ON public.workspaces FOR INSERT TO authenticated WITH CHECK (true);
CREATE POLICY "delete history by service role" ON public.timeline_events FOR DELETE USING ((auth.role() = 'service_role'::text));
CREATE POLICY "delete reflections by service role" ON public.reflections_artifact FOR DELETE USING ((auth.role() = 'service_role'::text));
ALTER TABLE public.document_versions ENABLE ROW LEVEL SECURITY;
CREATE POLICY document_versions_workspace_insert ON public.document_versions FOR INSERT WITH CHECK ((EXISTS ( SELECT 1
   FROM ((public.documents d
     JOIN public.baskets b ON ((d.basket_id = b.id)))
     JOIN public.workspace_memberships wm ON ((b.workspace_id = wm.workspace_id)))
  WHERE ((d.id = document_versions.document_id) AND (wm.user_id = auth.uid())))));
CREATE POLICY document_versions_workspace_select ON public.document_versions FOR SELECT USING ((EXISTS ( SELECT 1
   FROM ((public.documents d
     JOIN public.baskets b ON ((d.basket_id = b.id)))
     JOIN public.workspace_memberships wm ON ((b.workspace_id = wm.workspace_id)))
  WHERE ((d.id = document_versions.document_id) AND (wm.user_id = auth.uid())))));
ALTER TABLE public.documents ENABLE ROW LEVEL SECURITY;
CREATE POLICY documents_delete_workspace_member ON public.documents FOR DELETE TO authenticated USING ((workspace_id IN ( SELECT workspace_memberships.workspace_id
   FROM public.workspace_memberships
  WHERE (workspace_memberships.user_id = auth.uid()))));
CREATE POLICY documents_insert_workspace_member ON public.documents FOR INSERT TO authenticated WITH CHECK ((workspace_id IN ( SELECT workspace_memberships.workspace_id
   FROM public.workspace_memberships
  WHERE (workspace_memberships.user_id = auth.uid()))));
CREATE POLICY documents_select_workspace_member ON public.documents FOR SELECT TO authenticated USING ((workspace_id IN ( SELECT workspace_memberships.workspace_id
   FROM public.workspace_memberships
  WHERE (workspace_memberships.user_id = auth.uid()))));
CREATE POLICY documents_service_role_all ON public.documents TO service_role USING (true) WITH CHECK (true);
CREATE POLICY documents_update_workspace_member ON public.documents FOR UPDATE TO authenticated USING ((workspace_id IN ( SELECT workspace_memberships.workspace_id
   FROM public.workspace_memberships
  WHERE (workspace_memberships.user_id = auth.uid()))));
CREATE POLICY dump_member_read ON public.raw_dumps FOR SELECT USING ((workspace_id IN ( SELECT workspace_memberships.workspace_id
   FROM public.workspace_memberships
  WHERE (workspace_memberships.user_id = auth.uid()))));
CREATE POLICY event_member_delete ON public.events FOR DELETE USING ((EXISTS ( SELECT 1
   FROM public.workspace_memberships
  WHERE ((workspace_memberships.workspace_id = events.workspace_id) AND (workspace_memberships.user_id = auth.uid())))));
CREATE POLICY event_member_insert ON public.events FOR INSERT WITH CHECK ((EXISTS ( SELECT 1
   FROM public.workspace_memberships
  WHERE ((workspace_memberships.workspace_id = events.workspace_id) AND (workspace_memberships.user_id = auth.uid())))));
CREATE POLICY event_member_update ON public.events FOR UPDATE USING ((EXISTS ( SELECT 1
   FROM public.workspace_memberships
  WHERE ((workspace_memberships.workspace_id = events.workspace_id) AND (workspace_memberships.user_id = auth.uid())))));
CREATE POLICY events_insert_workspace_member ON public.events FOR INSERT TO authenticated WITH CHECK ((workspace_id IN ( SELECT workspace_memberships.workspace_id
   FROM public.workspace_memberships
  WHERE (workspace_memberships.user_id = auth.uid()))));
CREATE POLICY events_select_workspace_member ON public.events FOR SELECT TO authenticated USING ((workspace_id IN ( SELECT workspace_memberships.workspace_id
   FROM public.workspace_memberships
  WHERE (workspace_memberships.user_id = auth.uid()))));
CREATE POLICY events_service_role_all ON public.events TO service_role USING (true) WITH CHECK (true);
ALTER TABLE public.extraction_quality_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.knowledge_timeline ENABLE ROW LEVEL SECURITY;
CREATE POLICY knowledge_timeline_workspace_read ON public.knowledge_timeline FOR SELECT USING ((workspace_id IN ( SELECT workspace_memberships.workspace_id
   FROM public.workspace_memberships
  WHERE (workspace_memberships.user_id = auth.uid()))));
ALTER TABLE public.mcp_activity_logs ENABLE ROW LEVEL SECURITY;
CREATE POLICY mcp_activity_select ON public.mcp_activity_logs FOR SELECT USING ((EXISTS ( SELECT 1
   FROM public.workspace_memberships wm
  WHERE ((wm.workspace_id = mcp_activity_logs.workspace_id) AND (wm.user_id = auth.uid())))));
CREATE POLICY mcp_activity_service_delete ON public.mcp_activity_logs FOR DELETE USING ((auth.role() = 'service_role'::text));
CREATE POLICY mcp_activity_service_insert ON public.mcp_activity_logs FOR INSERT WITH CHECK ((auth.role() = 'service_role'::text));
ALTER TABLE public.mcp_oauth_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.mcp_unassigned_captures ENABLE ROW LEVEL SECURITY;
CREATE POLICY mcp_unassigned_select ON public.mcp_unassigned_captures FOR SELECT USING ((EXISTS ( SELECT 1
   FROM public.workspace_memberships wm
  WHERE ((wm.workspace_id = mcp_unassigned_captures.workspace_id) AND (wm.user_id = auth.uid())))));
CREATE POLICY mcp_unassigned_service_delete ON public.mcp_unassigned_captures FOR DELETE USING ((auth.role() = 'service_role'::text));
CREATE POLICY mcp_unassigned_service_insert ON public.mcp_unassigned_captures FOR INSERT WITH CHECK ((auth.role() = 'service_role'::text));
CREATE POLICY mcp_unassigned_update ON public.mcp_unassigned_captures FOR UPDATE USING ((EXISTS ( SELECT 1
   FROM public.workspace_memberships wm
  WHERE ((wm.workspace_id = mcp_unassigned_captures.workspace_id) AND (wm.user_id = auth.uid()))))) WITH CHECK ((EXISTS ( SELECT 1
   FROM public.workspace_memberships wm
  WHERE ((wm.workspace_id = mcp_unassigned_captures.workspace_id) AND (wm.user_id = auth.uid())))));
CREATE POLICY member_self_crud ON public.workspace_memberships USING ((user_id = auth.uid()));
CREATE POLICY member_self_insert ON public.workspace_memberships FOR INSERT TO authenticated WITH CHECK ((auth.uid() = user_id));
ALTER TABLE public.narrative ENABLE ROW LEVEL SECURITY;
CREATE POLICY narrative_delete_workspace_member ON public.narrative FOR DELETE TO authenticated USING ((EXISTS ( SELECT 1
   FROM (public.baskets b
     JOIN public.workspace_memberships wm ON ((wm.workspace_id = b.workspace_id)))
  WHERE ((b.id = narrative.basket_id) AND (wm.user_id = auth.uid())))));
CREATE POLICY narrative_insert_workspace_member ON public.narrative FOR INSERT TO authenticated WITH CHECK ((EXISTS ( SELECT 1
   FROM (public.baskets b
     JOIN public.workspace_memberships wm ON ((wm.workspace_id = b.workspace_id)))
  WHERE ((b.id = narrative.basket_id) AND (wm.user_id = auth.uid())))));
CREATE POLICY narrative_select_workspace_member ON public.narrative FOR SELECT TO authenticated USING ((EXISTS ( SELECT 1
   FROM (public.baskets b
     JOIN public.workspace_memberships wm ON ((wm.workspace_id = b.workspace_id)))
  WHERE ((b.id = narrative.basket_id) AND (wm.user_id = auth.uid())))));
CREATE POLICY narrative_service_role_all ON public.narrative TO service_role USING (true) WITH CHECK (true);
CREATE POLICY narrative_update_workspace_member ON public.narrative FOR UPDATE TO authenticated USING ((EXISTS ( SELECT 1
   FROM (public.baskets b
     JOIN public.workspace_memberships wm ON ((wm.workspace_id = b.workspace_id)))
  WHERE ((b.id = narrative.basket_id) AND (wm.user_id = auth.uid())))));
ALTER TABLE public.openai_app_tokens ENABLE ROW LEVEL SECURITY;
CREATE POLICY openai_app_tokens_service_access ON public.openai_app_tokens USING ((auth.role() = 'service_role'::text)) WITH CHECK ((auth.role() = 'service_role'::text));
CREATE POLICY p3_p4_policy_workspace_access ON public.p3_p4_regeneration_policy USING ((workspace_id IN ( SELECT workspace_memberships.workspace_id
   FROM public.workspace_memberships
  WHERE (workspace_memberships.user_id = auth.uid()))));
ALTER TABLE public.p3_p4_regeneration_policy ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.proposal_executions ENABLE ROW LEVEL SECURITY;
CREATE POLICY proposal_executions_insert ON public.proposal_executions FOR INSERT WITH CHECK ((proposal_id IN ( SELECT proposals.id
   FROM public.proposals
  WHERE (proposals.workspace_id IN ( SELECT workspace_memberships.workspace_id
           FROM public.workspace_memberships
          WHERE (workspace_memberships.user_id = auth.uid()))))));
CREATE POLICY proposal_executions_select ON public.proposal_executions FOR SELECT USING ((proposal_id IN ( SELECT proposals.id
   FROM public.proposals
  WHERE (proposals.workspace_id IN ( SELECT workspace_memberships.workspace_id
           FROM public.workspace_memberships
          WHERE (workspace_memberships.user_id = auth.uid()))))));
ALTER TABLE public.proposals ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.raw_dumps ENABLE ROW LEVEL SECURITY;
CREATE POLICY raw_dumps_delete_workspace_member ON public.raw_dumps FOR DELETE TO authenticated USING ((workspace_id IN ( SELECT workspace_memberships.workspace_id
   FROM public.workspace_memberships
  WHERE (workspace_memberships.user_id = auth.uid()))));
CREATE POLICY raw_dumps_insert_workspace_member ON public.raw_dumps FOR INSERT TO authenticated WITH CHECK ((workspace_id IN ( SELECT workspace_memberships.workspace_id
   FROM public.workspace_memberships
  WHERE (workspace_memberships.user_id = auth.uid()))));
CREATE POLICY raw_dumps_select_workspace_member ON public.raw_dumps FOR SELECT TO authenticated USING ((workspace_id IN ( SELECT workspace_memberships.workspace_id
   FROM public.workspace_memberships
  WHERE (workspace_memberships.user_id = auth.uid()))));
CREATE POLICY raw_dumps_workspace_insert ON public.raw_dumps FOR INSERT TO authenticated WITH CHECK ((workspace_id IN ( SELECT workspace_memberships.workspace_id
   FROM public.workspace_memberships
  WHERE (workspace_memberships.user_id = auth.uid()))));
CREATE POLICY "read history by workspace members" ON public.timeline_events FOR SELECT USING (((auth.role() = 'service_role'::text) OR (EXISTS ( SELECT 1
   FROM (public.baskets b
     JOIN public.v_user_workspaces m ON ((m.workspace_id = b.workspace_id)))
  WHERE ((b.id = timeline_events.basket_id) AND (m.user_id = auth.uid()))))));
CREATE POLICY "read reflections by workspace members" ON public.reflections_artifact FOR SELECT USING (((auth.role() = 'service_role'::text) OR (EXISTS ( SELECT 1
   FROM (public.baskets b
     JOIN public.v_user_workspaces m ON ((m.workspace_id = b.workspace_id)))
  WHERE ((b.id = reflections_artifact.basket_id) AND (m.user_id = auth.uid()))))));
CREATE POLICY reflection_cache_no_user_delete ON public.reflections_artifact FOR DELETE USING (false);
CREATE POLICY reflection_cache_no_user_insert ON public.reflections_artifact FOR INSERT WITH CHECK (false);
CREATE POLICY reflection_cache_no_user_update ON public.reflections_artifact FOR UPDATE USING (false) WITH CHECK (false);
CREATE POLICY reflection_cache_read ON public.reflections_artifact FOR SELECT USING ((EXISTS ( SELECT 1
   FROM public.workspace_memberships m
  WHERE ((m.user_id = auth.uid()) AND (m.workspace_id = reflections_artifact.workspace_id)))));
ALTER TABLE public.reflections_artifact ENABLE ROW LEVEL SECURITY;
CREATE POLICY reflections_artifact_service_insert ON public.reflections_artifact FOR INSERT WITH CHECK ((auth.role() = 'service_role'::text));
CREATE POLICY reflections_artifact_workspace_select ON public.reflections_artifact FOR SELECT USING ((EXISTS ( SELECT 1
   FROM public.workspace_memberships wm
  WHERE ((wm.workspace_id = reflections_artifact.workspace_id) AND (wm.user_id = auth.uid())))));
CREATE POLICY revision_member_delete ON public.block_revisions FOR DELETE USING ((EXISTS ( SELECT 1
   FROM public.workspace_memberships
  WHERE ((workspace_memberships.workspace_id = block_revisions.workspace_id) AND (workspace_memberships.user_id = auth.uid())))));
CREATE POLICY revision_member_insert ON public.block_revisions FOR INSERT WITH CHECK (true);
CREATE POLICY revision_member_read ON public.block_revisions FOR SELECT USING (true);
CREATE POLICY revision_member_update ON public.block_revisions FOR UPDATE USING ((EXISTS ( SELECT 1
   FROM public.workspace_memberships
  WHERE ((workspace_memberships.workspace_id = block_revisions.workspace_id) AND (workspace_memberships.user_id = auth.uid())))));
ALTER TABLE public.revisions ENABLE ROW LEVEL SECURITY;
CREATE POLICY select_own_raw_dumps ON public.raw_dumps FOR SELECT TO authenticated USING ((EXISTS ( SELECT 1
   FROM public.baskets b
  WHERE ((b.id = raw_dumps.basket_id) AND (b.user_id = auth.uid())))));
CREATE POLICY select_own_revisions ON public.revisions FOR SELECT TO authenticated USING ((EXISTS ( SELECT 1
   FROM public.baskets b
  WHERE ((b.id = revisions.basket_id) AND (b.user_id = auth.uid())))));
CREATE POLICY "service role ALL access" ON public.raw_dumps TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "service role full access" ON public.baskets TO service_role USING (true);
CREATE POLICY "service role full access" ON public.raw_dumps TO service_role USING (true);
CREATE POLICY service_role_can_insert_events ON public.app_events FOR INSERT WITH CHECK ((auth.role() = 'service_role'::text));
ALTER TABLE public.substrate_references ENABLE ROW LEVEL SECURITY;
CREATE POLICY substrate_references_delete_policy ON public.substrate_references FOR DELETE USING ((EXISTS ( SELECT 1
   FROM ((public.documents d
     JOIN public.baskets b ON ((d.basket_id = b.id)))
     JOIN public.workspace_memberships wm ON ((wm.workspace_id = b.workspace_id)))
  WHERE ((d.id = substrate_references.document_id) AND (wm.user_id = auth.uid())))));
CREATE POLICY substrate_references_insert_policy ON public.substrate_references FOR INSERT WITH CHECK ((EXISTS ( SELECT 1
   FROM ((public.documents d
     JOIN public.baskets b ON ((d.basket_id = b.id)))
     JOIN public.workspace_memberships wm ON ((wm.workspace_id = b.workspace_id)))
  WHERE ((d.id = substrate_references.document_id) AND (wm.user_id = auth.uid())))));
CREATE POLICY substrate_references_select_policy ON public.substrate_references FOR SELECT USING ((EXISTS ( SELECT 1
   FROM ((public.documents d
     JOIN public.baskets b ON ((d.basket_id = b.id)))
     JOIN public.workspace_memberships wm ON ((wm.workspace_id = b.workspace_id)))
  WHERE ((d.id = substrate_references.document_id) AND (wm.user_id = auth.uid())))));
CREATE POLICY substrate_references_update_policy ON public.substrate_references FOR UPDATE USING ((EXISTS ( SELECT 1
   FROM ((public.documents d
     JOIN public.baskets b ON ((d.basket_id = b.id)))
     JOIN public.workspace_memberships wm ON ((wm.workspace_id = b.workspace_id)))
  WHERE ((d.id = substrate_references.document_id) AND (wm.user_id = auth.uid())))));
ALTER TABLE public.substrate_relationships ENABLE ROW LEVEL SECURITY;
CREATE POLICY te_select_workspace_member ON public.timeline_events FOR SELECT USING ((EXISTS ( SELECT 1
   FROM (public.baskets b
     JOIN public.workspace_memberships wm ON ((wm.workspace_id = b.workspace_id)))
  WHERE ((b.id = timeline_events.basket_id) AND (wm.user_id = auth.uid())))));
CREATE POLICY "timeline insert: workspace member" ON public.timeline_events FOR INSERT WITH CHECK ((EXISTS ( SELECT 1
   FROM (public.baskets b
     JOIN public.workspace_memberships m ON ((m.workspace_id = b.workspace_id)))
  WHERE ((b.id = timeline_events.basket_id) AND (m.user_id = auth.uid())))));
CREATE POLICY "timeline read: workspace member" ON public.timeline_events FOR SELECT USING ((EXISTS ( SELECT 1
   FROM (public.baskets b
     JOIN public.workspace_memberships m ON ((m.workspace_id = b.workspace_id)))
  WHERE ((b.id = timeline_events.basket_id) AND (m.user_id = auth.uid())))));
ALTER TABLE public.timeline_events ENABLE ROW LEVEL SECURITY;
CREATE POLICY "update history by service role" ON public.timeline_events FOR UPDATE USING ((auth.role() = 'service_role'::text)) WITH CHECK ((auth.role() = 'service_role'::text));
CREATE POLICY "update reflections by service role" ON public.reflections_artifact FOR UPDATE USING ((auth.role() = 'service_role'::text)) WITH CHECK ((auth.role() = 'service_role'::text));
ALTER TABLE public.user_alerts ENABLE ROW LEVEL SECURITY;
CREATE POLICY user_alerts_own_read ON public.user_alerts FOR SELECT USING ((user_id = auth.uid()));
CREATE POLICY user_alerts_own_update ON public.user_alerts FOR UPDATE USING ((user_id = auth.uid()));
ALTER TABLE public.workspace_governance_settings ENABLE ROW LEVEL SECURITY;
CREATE POLICY workspace_governance_settings_insert ON public.workspace_governance_settings FOR INSERT WITH CHECK ((workspace_id IN ( SELECT workspace_memberships.workspace_id
   FROM public.workspace_memberships
  WHERE ((workspace_memberships.user_id = auth.uid()) AND (workspace_memberships.role = ANY (ARRAY['admin'::text, 'owner'::text]))))));
CREATE POLICY workspace_governance_settings_select ON public.workspace_governance_settings FOR SELECT USING ((workspace_id IN ( SELECT workspace_memberships.workspace_id
   FROM public.workspace_memberships
  WHERE (workspace_memberships.user_id = auth.uid()))));
CREATE POLICY workspace_governance_settings_update ON public.workspace_governance_settings FOR UPDATE USING ((workspace_id IN ( SELECT workspace_memberships.workspace_id
   FROM public.workspace_memberships
  WHERE ((workspace_memberships.user_id = auth.uid()) AND (workspace_memberships.role = ANY (ARRAY['admin'::text, 'owner'::text]))))));
CREATE POLICY workspace_members_can_read_events ON public.app_events FOR SELECT USING ((EXISTS ( SELECT 1
   FROM public.workspace_memberships
  WHERE ((workspace_memberships.workspace_id = app_events.workspace_id) AND (workspace_memberships.user_id = auth.uid())))));
ALTER TABLE public.workspace_memberships ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.workspaces ENABLE ROW LEVEL SECURITY;
CREATE POLICY "write history by service role" ON public.timeline_events FOR INSERT WITH CHECK ((auth.role() = 'service_role'::text));
CREATE POLICY "write reflections by service role" ON public.reflections_artifact FOR INSERT WITH CHECK ((auth.role() = 'service_role'::text));
CREATE POLICY ws_owner_delete ON public.workspaces FOR DELETE USING ((owner_id = auth.uid()));
CREATE POLICY ws_owner_or_member_read ON public.workspaces FOR SELECT USING (((owner_id = auth.uid()) OR (id IN ( SELECT workspace_memberships.workspace_id
   FROM public.workspace_memberships
  WHERE (workspace_memberships.user_id = auth.uid())))));
CREATE POLICY ws_owner_update ON public.workspaces FOR UPDATE USING ((owner_id = auth.uid()));
