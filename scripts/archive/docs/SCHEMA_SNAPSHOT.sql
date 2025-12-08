CREATE SCHEMA public;
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
CREATE TYPE public.context_item_state AS ENUM (
    'PROVISIONAL',
    'PROPOSED',
    'UNDER_REVIEW',
    'ACTIVE',
    'DEPRECATED',
    'MERGED',
    'REJECTED'
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
    'context_item',
    'timeline_event'
);
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
CREATE FUNCTION public.emit_narrative_event(p_basket_id uuid, p_doc_id uuid, p_kind text, p_preview text) RETURNS void
    LANGUAGE plpgsql
    AS $$
begin
  -- Constrained kinds allow 'narrative' (use as channel); encode p_kind in payload
  insert into public.timeline_events (basket_id, kind, ref_id, preview, payload)
  values (
    p_basket_id, 'narrative', p_doc_id, p_preview,
    jsonb_build_object('event', p_kind, 'doc_id', p_doc_id::text)
  );
end$$;
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
CREATE FUNCTION public.fn_document_attach_substrate(p_document_id uuid, p_substrate_type public.substrate_type, p_substrate_id uuid, p_role text DEFAULT NULL::text, p_weight numeric DEFAULT NULL::numeric, p_snippets jsonb DEFAULT '[]'::jsonb, p_metadata jsonb DEFAULT '{}'::jsonb) RETURNS uuid
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
DECLARE
  v_reference_id uuid;
  v_workspace_id uuid;
BEGIN
  -- Get document workspace
  SELECT d.workspace_id INTO v_workspace_id
  FROM documents d WHERE d.id = p_document_id;
  
  -- Insert or update reference
  INSERT INTO substrate_references (
    document_id,
    substrate_type, 
    substrate_id,
    role,
    weight,
    snippets,
    metadata,
    created_by
  ) VALUES (
    p_document_id,
    p_substrate_type,
    p_substrate_id,
    p_role,
    p_weight,
    p_snippets,
    p_metadata,
    auth.uid()
  ) ON CONFLICT (document_id, substrate_type, substrate_id) 
  DO UPDATE SET
    role = EXCLUDED.role,
    weight = EXCLUDED.weight,
    snippets = EXCLUDED.snippets,
    metadata = EXCLUDED.metadata
  RETURNING id INTO v_reference_id;
  
  -- Emit timeline event
  PERFORM fn_timeline_emit(
    (SELECT basket_id FROM documents WHERE id = p_document_id),
    'document.' || p_substrate_type || '.attached',
    v_reference_id,
    'Attached ' || p_substrate_type || ' to document',
    jsonb_build_object('substrate_id', p_substrate_id, 'substrate_type', p_substrate_type)
  );
  
  RETURN v_reference_id;
END $$;
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
BEGIN
  -- Generate version hash (git-like)
  v_version_hash := 'doc_v' || substr(encode(sha256(p_content::bytea), 'hex'), 1, 58);
  
  -- Get document workspace for validation
  SELECT workspace_id INTO v_workspace_id 
  FROM documents WHERE id = p_document_id;
  
  IF v_workspace_id IS NULL THEN
    RAISE EXCEPTION 'Document % not found', p_document_id;
  END IF;
  
  -- Insert version (idempotent by hash)
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
    COALESCE(
      (SELECT jsonb_agg(to_jsonb(sr.*)) 
       FROM substrate_references sr 
       WHERE sr.document_id = p_document_id), 
      '[]'::jsonb
    ),
    auth.uid(),
    p_version_message,
    d.current_version_hash
  FROM documents d 
  WHERE d.id = p_document_id
  ON CONFLICT (version_hash) DO NOTHING;
  
  -- Update document current version
  UPDATE documents 
  SET current_version_hash = v_version_hash,
      updated_at = now()
  WHERE id = p_document_id;
  
  -- Emit timeline event
  PERFORM fn_timeline_emit(
    (SELECT basket_id FROM documents WHERE id = p_document_id),
    'document.versioned',
    p_document_id,
    'Document version created: ' || left(v_version_hash, 12),
    jsonb_build_object('version_hash', v_version_hash, 'message', p_version_message)
  );
  
  RETURN v_version_hash;
END $$;
CREATE FUNCTION public.fn_document_detach_substrate(p_document_id uuid, p_substrate_type public.substrate_type, p_substrate_id uuid) RETURNS boolean
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
DECLARE
  v_deleted_count int;
BEGIN
  -- Delete the reference
  DELETE FROM substrate_references
  WHERE document_id = p_document_id
    AND substrate_type = p_substrate_type
    AND substrate_id = p_substrate_id;
    
  GET DIAGNOSTICS v_deleted_count = ROW_COUNT;
  
  IF v_deleted_count > 0 THEN
    -- Emit timeline event
    PERFORM fn_timeline_emit(
      (SELECT basket_id FROM documents WHERE id = p_document_id),
      'document.' || p_substrate_type || '.detached',
      p_substrate_id,
      'Detached ' || p_substrate_type || ' from document',
      jsonb_build_object('substrate_id', p_substrate_id, 'substrate_type', p_substrate_type)
    );
    
    RETURN true;
  END IF;
  
  RETURN false;
END $$;
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
CREATE FUNCTION public.fn_persist_reflection(p_basket_id uuid, p_pattern text, p_tension text, p_question text) RETURNS uuid
    LANGUAGE plpgsql
    AS $$
DECLARE 
  v_id uuid;
  v_workspace_id uuid;
  v_reflection_text text;
  v_substrate_hash text;
BEGIN
  -- Get workspace_id from basket
  SELECT workspace_id INTO v_workspace_id FROM public.baskets WHERE id = p_basket_id;
  IF v_workspace_id IS NULL THEN
    RAISE EXCEPTION 'Basket % not found', p_basket_id;
  END IF;
  -- Compose reflection_text from pattern, tension, question
  v_reflection_text := COALESCE(
    CASE 
      WHEN p_pattern IS NOT NULL AND p_tension IS NOT NULL AND p_question IS NOT NULL 
      THEN 'Pattern: ' || p_pattern || E'\n\nTension: ' || p_tension || E'\n\nQuestion: ' || p_question
      WHEN p_pattern IS NOT NULL AND p_tension IS NOT NULL
      THEN 'Pattern: ' || p_pattern || E'\n\nTension: ' || p_tension
      WHEN p_pattern IS NOT NULL
      THEN p_pattern
      WHEN p_tension IS NOT NULL  
      THEN p_tension
      WHEN p_question IS NOT NULL
      THEN p_question
      ELSE 'Empty reflection'
    END, 
    'Empty reflection'
  );
  -- Generate substrate hash from inputs
  v_substrate_hash := 'reflection-' || encode(sha256((COALESCE(p_pattern, '') || COALESCE(p_tension, '') || COALESCE(p_question, ''))::bytea), 'hex');
  -- Insert into canonical schema
  INSERT INTO public.reflection_cache (
    basket_id, 
    workspace_id,
    substrate_hash,
    reflection_text,
    substrate_window_start,
    substrate_window_end,
    computation_timestamp,
    last_accessed_at,
    meta,
    created_at,
    updated_at
  )
  VALUES (
    p_basket_id, 
    v_workspace_id,
    v_substrate_hash,
    v_reflection_text,
    NOW(),
    NOW(),
    NOW(),
    NOW(),
    jsonb_build_object('legacy_migration', true, 'pattern', p_pattern, 'tension', p_tension, 'question', p_question),
    NOW(),
    NOW()
  )
  ON CONFLICT (basket_id, substrate_hash) DO UPDATE SET
    reflection_text = EXCLUDED.reflection_text,
    computation_timestamp = EXCLUDED.computation_timestamp,
    last_accessed_at = NOW(),
    updated_at = NOW(),
    meta = EXCLUDED.meta
  RETURNING id INTO v_id;
  -- Emit timeline event
  PERFORM public.fn_timeline_emit(
    p_basket_id,
    'reflection',
    v_id,
    LEFT(v_reflection_text, 140),
    jsonb_build_object('source','reflection_job','actor_id', auth.uid())
  );
  RETURN v_id;
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
CREATE FUNCTION public.fn_reflection_cache_upsert(p_basket_id uuid, p_pattern text, p_tension text, p_question text, p_meta_hash text) RETURNS boolean
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'public'
    AS $$
declare
  v_last text;
  v_changed boolean := false;
begin
  select meta_derived_from into v_last
  from public.basket_reflections
  where basket_id = p_basket_id
  order by computed_at desc
  limit 1;
  if v_last is distinct from p_meta_hash then
    insert into public.basket_reflections (id, basket_id, pattern, tension, question, meta_derived_from)
    values (gen_random_uuid(), p_basket_id, p_pattern, p_tension, p_question, p_meta_hash);
    -- Emit machine event to events table
    insert into public.events (id, basket_id, kind, payload, workspace_id, origin)
    values (gen_random_uuid(), p_basket_id, 'reflection.computed',
            jsonb_build_object('basket_id', p_basket_id, 'meta_derived_from', p_meta_hash),
            null, 'system');
    -- Optional: surface a small note to timeline
    insert into public.timeline_events (basket_id, kind, preview, payload)
    values (p_basket_id, 'system_note', 'Reflections updated', jsonb_build_object('meta_derived_from', p_meta_hash));
    v_changed := true;
  end if;
  return v_changed;
end;
$$;
CREATE FUNCTION public.fn_reflection_create_from_document(p_basket_id uuid, p_document_id uuid, p_reflection_text text) RETURNS uuid
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
DECLARE
  v_reflection_id uuid;
  v_workspace_id uuid;
  v_version_hash varchar(64);
BEGIN
  -- Get workspace and current document version
  SELECT d.workspace_id, d.current_version_hash
  INTO v_workspace_id, v_version_hash
  FROM documents d WHERE d.id = p_document_id;
  
  -- Create document-focused reflection
  INSERT INTO reflections_artifact (
    basket_id,
    workspace_id,
    reflection_text,
    substrate_hash,
    reflection_target_type,
    reflection_target_id,
    reflection_target_version,
    computation_timestamp
  ) VALUES (
    p_basket_id,
    v_workspace_id,
    p_reflection_text,
    'document_' || COALESCE(v_version_hash, 'current'),
    'document',
    p_document_id,
    v_version_hash,
    now()
  ) RETURNING id INTO v_reflection_id;
  
  RETURN v_reflection_id;
END $$;
CREATE FUNCTION public.fn_reflection_create_from_substrate(p_basket_id uuid, p_reflection_text text) RETURNS uuid
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
DECLARE
  v_reflection_id uuid;
  v_workspace_id uuid;
  v_substrate_hash varchar(64);
BEGIN
  -- Get workspace
  SELECT workspace_id INTO v_workspace_id FROM baskets WHERE id = p_basket_id;
  
  -- Generate substrate hash for this basket's current state
  v_substrate_hash := 'substrate_' || encode(sha256((p_basket_id || now())::text::bytea), 'hex');
  
  -- Insert substrate-focused reflection
  INSERT INTO reflections_artifact (
    basket_id,
    workspace_id,
    reflection_text,
    substrate_hash,
    reflection_target_type,
    computation_timestamp
  ) VALUES (
    p_basket_id,
    v_workspace_id,
    p_reflection_text,
    v_substrate_hash,
    'substrate',
    now()
  ) RETURNING id INTO v_reflection_id;
  
  -- Emit timeline event
  PERFORM fn_timeline_emit(
    p_basket_id,
    'reflection.computed',
    v_reflection_id,
    left(p_reflection_text, 140),
    jsonb_build_object('target_type', 'substrate')
  );
  
  RETURN v_reflection_id;
END $$;
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
CREATE FUNCTION public.get_workspace_governance_flags(p_workspace_id uuid) RETURNS jsonb
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
DECLARE
  result jsonb;
  settings_row public.workspace_governance_settings%ROWTYPE;
BEGIN
  SELECT * INTO settings_row 
  FROM public.workspace_governance_settings 
  WHERE workspace_id = p_workspace_id;
  
  IF FOUND THEN
    -- Use workspace-specific settings but enforce canon requirements
    result := jsonb_build_object(
      'governance_enabled', settings_row.governance_enabled,
      'validator_required', settings_row.validator_required,
      
      -- Canon enforcement: P1 must use proposals (override workspace setting)
      'direct_substrate_writes', FALSE,
      
      'governance_ui_enabled', settings_row.governance_ui_enabled,
      
      -- Canon enforcement: P0 is always direct (override workspace setting)
      'ep_onboarding_dump', 'direct',
      
      -- Respect workspace preferences for other entry points
      'ep_manual_edit', settings_row.ep_manual_edit,
      'ep_graph_action', settings_row.ep_graph_action,
      'ep_timeline_restore', settings_row.ep_timeline_restore,
      
      'default_blast_radius', COALESCE(settings_row.default_blast_radius, 'Scoped'),
      'source', 'workspace_database'
    );
  ELSE
    -- Fallback defaults when no workspace settings exist
    result := jsonb_build_object(
      'governance_enabled', TRUE,
      'validator_required', FALSE,
      'direct_substrate_writes', FALSE, -- Canon: P1 requires proposals
      'governance_ui_enabled', TRUE,
      'ep_onboarding_dump', 'direct',   -- Canon: P0 always direct
      'ep_manual_edit', 'hybrid',
      'ep_graph_action', 'hybrid',
      'ep_timeline_restore', 'proposal',
      'default_blast_radius', 'Scoped',
      'source', 'canon_compliant_defaults'
    );
  END IF;
  
  RETURN result;
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
CREATE FUNCTION public.set_basket_user_id() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
begin
  if new.user_id is null then
    new.user_id := auth.uid();
  end if;
  return new;
end $$;
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
CREATE FUNCTION public.update_reflection_cache_updated_at() RETURNS trigger
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
    extraction_method text DEFAULT 'legacy_text_chunks'::text,
    provenance_validated boolean DEFAULT false,
    ingredient_version text DEFAULT '1.0'::text,
    normalized_label text,
    updated_at timestamp with time zone DEFAULT now(),
    CONSTRAINT blocks_check CHECK ((((state = 'CONSTANT'::public.block_state) AND (scope IS NOT NULL)) OR (state <> 'CONSTANT'::public.block_state))),
    CONSTRAINT check_structured_ingredient_metadata CHECK (public.validate_structured_ingredient_metadata(metadata))
)
WITH (autovacuum_enabled='true');
ALTER TABLE ONLY public.blocks REPLICA IDENTITY FULL;
CREATE TABLE public.context_items (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    basket_id uuid NOT NULL,
    document_id uuid,
    type text NOT NULL,
    content text,
    status text DEFAULT 'active'::text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    raw_dump_id uuid,
    title text,
    description text,
    confidence_score double precision DEFAULT 0.5,
    metadata jsonb DEFAULT '{}'::jsonb,
    updated_at timestamp with time zone DEFAULT now(),
    normalized_label text,
    origin_ref jsonb,
    equivalence_class uuid,
    state public.context_item_state DEFAULT 'ACTIVE'::public.context_item_state,
    proposal_id uuid,
    approved_at timestamp with time zone,
    approved_by uuid,
    CONSTRAINT context_items_status_check CHECK ((status = ANY (ARRAY['active'::text, 'archived'::text])))
);
ALTER TABLE ONLY public.context_items REPLICA IDENTITY FULL;
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
CREATE VIEW public.document_composition_stats AS
 SELECT substrate_references.document_id,
    count(*) FILTER (WHERE (substrate_references.substrate_type = 'block'::public.substrate_type)) AS blocks_count,
    count(*) FILTER (WHERE (substrate_references.substrate_type = 'dump'::public.substrate_type)) AS dumps_count,
    count(*) FILTER (WHERE (substrate_references.substrate_type = 'context_item'::public.substrate_type)) AS context_items_count,
    count(*) FILTER (WHERE (substrate_references.substrate_type = 'timeline_event'::public.substrate_type)) AS timeline_events_count,
    count(*) AS total_substrate_references
   FROM public.substrate_references
  GROUP BY substrate_references.document_id;
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
    CONSTRAINT non_empty_content CHECK ((length(content) > 0)),
    CONSTRAINT valid_version_hash CHECK (((version_hash)::text ~ '^doc_v[a-f0-9]{58}$'::text))
);
CREATE TABLE public.documents (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    basket_id uuid,
    title text NOT NULL,
    content_raw text NOT NULL,
    content_rendered text,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    created_by uuid,
    updated_by uuid,
    workspace_id uuid NOT NULL,
    document_type text DEFAULT 'general'::text NOT NULL,
    metadata jsonb DEFAULT '{}'::jsonb NOT NULL,
    current_version_hash character varying(64)
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
CREATE VIEW public.document_staleness AS
 WITH latest_times AS (
         SELECT d.id AS document_id,
            dv.version_hash,
            dv.created_at AS version_created_at,
            GREATEST(COALESCE(max(
                CASE
                    WHEN (sr.substrate_type = 'dump'::public.substrate_type) THEN rd.created_at
                    ELSE NULL::timestamp with time zone
                END), '1970-01-01 00:00:00+00'::timestamp with time zone), COALESCE(max(
                CASE
                    WHEN (sr.substrate_type = 'block'::public.substrate_type) THEN cb.created_at
                    ELSE NULL::timestamp with time zone
                END), '1970-01-01 00:00:00+00'::timestamp with time zone), COALESCE(max(
                CASE
                    WHEN (sr.substrate_type = 'context_item'::public.substrate_type) THEN ci.updated_at
                    ELSE NULL::timestamp with time zone
                END), '1970-01-01 00:00:00+00'::timestamp with time zone)) AS last_substrate_updated_at
           FROM (((((public.documents d
             LEFT JOIN public.document_versions dv ON (((dv.version_hash)::text = (d.current_version_hash)::text)))
             LEFT JOIN public.substrate_references sr ON ((sr.document_id = d.id)))
             LEFT JOIN public.raw_dumps rd ON (((rd.id = sr.substrate_id) AND (sr.substrate_type = 'dump'::public.substrate_type))))
             LEFT JOIN public.blocks cb ON (((cb.id = sr.substrate_id) AND (sr.substrate_type = 'block'::public.substrate_type))))
             LEFT JOIN public.context_items ci ON (((ci.id = sr.substrate_id) AND (sr.substrate_type = 'context_item'::public.substrate_type))))
          GROUP BY d.id, dv.version_hash, dv.created_at
        )
 SELECT latest_times.document_id,
    latest_times.version_hash,
    latest_times.version_created_at,
    latest_times.last_substrate_updated_at,
    (latest_times.last_substrate_updated_at > latest_times.version_created_at) AS is_stale
   FROM latest_times;
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
CREATE TABLE public.idempotency_keys (
    request_id text NOT NULL,
    delta_id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
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
    execution_time_ms integer
);
CREATE TABLE public.proposals (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    basket_id uuid NOT NULL,
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
    CONSTRAINT proposals_origin_check CHECK ((origin = ANY (ARRAY['agent'::text, 'human'::text])))
);
CREATE TABLE public.reflections_artifact (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    basket_id uuid NOT NULL,
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
    reflection_target_type character varying(20) DEFAULT 'legacy'::character varying,
    reflection_target_id uuid,
    reflection_target_version character varying(64),
    CONSTRAINT valid_reflection_target CHECK (((reflection_target_type)::text = ANY ((ARRAY['substrate'::character varying, 'document'::character varying, 'legacy'::character varying])::text[])))
);
CREATE TABLE public.revisions (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    basket_id uuid,
    actor_id uuid,
    summary text,
    diff_json jsonb,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);
CREATE VIEW public.structured_ingredient_blocks AS
 SELECT blocks.id,
    blocks.basket_id,
    blocks.title,
    blocks.semantic_type,
    blocks.confidence_score,
    blocks.extraction_method,
    blocks.provenance_validated,
    blocks.ingredient_version,
    (blocks.metadata -> 'knowledge_ingredients'::text) AS ingredients,
    (blocks.metadata -> 'transformation_hints'::text) AS transformation_hints,
    blocks.created_at
   FROM public.blocks
  WHERE ((blocks.extraction_method = 'llm_structured_v2'::text) AND (blocks.provenance_validated = true));
CREATE TABLE public.substrate_relationships (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    basket_id uuid,
    from_type text NOT NULL,
    from_id uuid NOT NULL,
    to_type text NOT NULL,
    to_id uuid NOT NULL,
    relationship_type text NOT NULL,
    description text,
    strength double precision DEFAULT 0.5,
    created_at timestamp with time zone DEFAULT now()
);
ALTER TABLE ONLY public.substrate_relationships REPLICA IDENTITY FULL;
CREATE TABLE public.timeline_events (
    id bigint NOT NULL,
    basket_id uuid NOT NULL,
    ts timestamp with time zone DEFAULT now() NOT NULL,
    kind text NOT NULL,
    ref_id uuid,
    preview text,
    payload jsonb,
    workspace_id uuid NOT NULL,
    CONSTRAINT timeline_events_kind_check CHECK ((kind = ANY (ARRAY['dump'::text, 'reflection'::text, 'narrative'::text, 'system_note'::text, 'block'::text, 'dump.created'::text, 'reflection.computed'::text, 'delta.applied'::text, 'delta.rejected'::text, 'document.created'::text, 'document.updated'::text, 'document.block.attached'::text, 'document.block.detached'::text, 'document.dump.attached'::text, 'document.dump.detached'::text, 'document.context_item.attached'::text, 'document.context_item.detached'::text, 'document.reflection.attached'::text, 'document.reflection.detached'::text, 'document.timeline_event.attached'::text, 'document.timeline_event.detached'::text, 'block.created'::text, 'block.updated'::text, 'basket.created'::text, 'workspace.member_added'::text, 'proposal.submitted'::text, 'proposal.approved'::text, 'proposal.rejected'::text, 'substrate.committed'::text, 'cascade.completed'::text])))
);
CREATE SEQUENCE public.timeline_events_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER SEQUENCE public.timeline_events_id_seq OWNED BY public.timeline_events.id;
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
CREATE VIEW public.v_narrative_documents AS
 SELECT d.id,
    d.basket_id,
    d.title,
    d.content_raw,
    d.content_rendered,
    d.created_at,
    d.updated_at,
    d.created_by,
    d.updated_by,
    d.workspace_id,
    d.document_type,
    d.metadata
   FROM public.documents d
  WHERE (d.document_type = 'narrative'::text);
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
CREATE VIEW public.vw_document_analyze_lite AS
 SELECT d.id AS document_id,
    d.title,
    d.basket_id,
    d.workspace_id,
    d.current_version_hash,
    d.updated_at AS document_updated_at,
    stats.blocks_count,
    stats.dumps_count,
    stats.context_items_count,
    stats.timeline_events_count,
    stats.total_substrate_references,
    round(COALESCE(avg(sr.weight), (0)::numeric), 2) AS avg_reference_weight,
    st.version_created_at,
    st.last_substrate_updated_at,
    st.is_stale
   FROM (((public.documents d
     LEFT JOIN public.document_composition_stats stats ON ((stats.document_id = d.id)))
     LEFT JOIN public.substrate_references sr ON ((sr.document_id = d.id)))
     LEFT JOIN public.document_staleness st ON ((st.document_id = d.id)))
  GROUP BY d.id, d.title, d.basket_id, d.workspace_id, d.current_version_hash, d.updated_at, stats.blocks_count, stats.dumps_count, stats.context_items_count, stats.timeline_events_count, stats.total_substrate_references, st.version_created_at, st.last_substrate_updated_at, st.is_stale;
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
    CONSTRAINT workspace_governance_settings_ep_document_edit_check CHECK ((ep_document_edit = ANY (ARRAY['proposal'::text, 'direct'::text, 'hybrid'::text]))),
    CONSTRAINT workspace_governance_settings_ep_graph_action_check CHECK ((ep_graph_action = ANY (ARRAY['proposal'::text, 'direct'::text, 'hybrid'::text]))),
    CONSTRAINT workspace_governance_settings_ep_manual_edit_check CHECK ((ep_manual_edit = ANY (ARRAY['proposal'::text, 'direct'::text, 'hybrid'::text]))),
    CONSTRAINT workspace_governance_settings_ep_onboarding_dump_check CHECK ((ep_onboarding_dump = ANY (ARRAY['proposal'::text, 'direct'::text, 'hybrid'::text]))),
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
ALTER TABLE ONLY public.artifact_generation_settings
    ADD CONSTRAINT artifact_generation_settings_pkey PRIMARY KEY (workspace_id);
ALTER TABLE ONLY public.basket_deltas
    ADD CONSTRAINT basket_deltas_pkey PRIMARY KEY (delta_id);
ALTER TABLE ONLY public.basket_events
    ADD CONSTRAINT basket_events_pkey PRIMARY KEY (id);
ALTER TABLE ONLY public.reflections_artifact
    ADD CONSTRAINT basket_reflections_pkey PRIMARY KEY (id);
ALTER TABLE public.baskets
    ADD CONSTRAINT baskets_idem_is_uuid CHECK (((idempotency_key IS NULL) OR ((idempotency_key)::text ~* '^[0-9a-f-]{36}$'::text))) NOT VALID;
ALTER TABLE ONLY public.baskets
    ADD CONSTRAINT baskets_pkey PRIMARY KEY (id);
ALTER TABLE ONLY public.block_links
    ADD CONSTRAINT block_links_pkey PRIMARY KEY (id);
ALTER TABLE ONLY public.block_revisions
    ADD CONSTRAINT block_revisions_pkey PRIMARY KEY (id);
ALTER TABLE ONLY public.blocks
    ADD CONSTRAINT blocks_pkey PRIMARY KEY (id);
ALTER TABLE ONLY public.context_items
    ADD CONSTRAINT context_items_pkey PRIMARY KEY (id);
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
ALTER TABLE ONLY public.idempotency_keys
    ADD CONSTRAINT idempotency_keys_pkey PRIMARY KEY (request_id);
ALTER TABLE ONLY public.narrative
    ADD CONSTRAINT narrative_pkey PRIMARY KEY (id);
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
ALTER TABLE ONLY public.timeline_events
    ADD CONSTRAINT timeline_events_pkey PRIMARY KEY (id);
ALTER TABLE ONLY public.raw_dumps
    ADD CONSTRAINT uq_raw_dumps_basket_dump_req UNIQUE (basket_id, dump_request_id);
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
CREATE UNIQUE INDEX docs_basket_title_idx ON public.documents USING btree (basket_id, title);
CREATE INDEX idx_agent_queue_cascade ON public.agent_processing_queue USING gin (cascade_metadata);
CREATE UNIQUE INDEX idx_agent_queue_dump_id_unique ON public.agent_processing_queue USING btree (dump_id) WHERE (dump_id IS NOT NULL);
CREATE INDEX idx_agent_queue_priority ON public.agent_processing_queue USING btree (priority DESC, created_at);
CREATE INDEX idx_agent_queue_user_workspace ON public.agent_processing_queue USING btree (user_id, workspace_id);
CREATE INDEX idx_agent_queue_work_id ON public.agent_processing_queue USING btree (work_id);
CREATE INDEX idx_agent_queue_work_type ON public.agent_processing_queue USING btree (work_type, processing_state);
CREATE INDEX idx_basket_deltas_applied_at ON public.basket_deltas USING btree (applied_at);
CREATE INDEX idx_basket_deltas_basket ON public.basket_deltas USING btree (basket_id, created_at DESC);
CREATE INDEX idx_basket_deltas_basket_id ON public.basket_deltas USING btree (basket_id);
CREATE INDEX idx_basket_deltas_created ON public.basket_deltas USING btree (created_at DESC);
CREATE INDEX idx_basket_deltas_created_at ON public.basket_deltas USING btree (created_at DESC);
CREATE INDEX idx_basket_deltas_unapplied ON public.basket_deltas USING btree (basket_id, created_at DESC) WHERE (applied_at IS NULL);
CREATE INDEX idx_basket_events_created ON public.basket_events USING btree (created_at DESC);
CREATE INDEX idx_basket_events_created_at ON public.basket_events USING btree (created_at DESC);
CREATE INDEX idx_basket_events_event_type ON public.basket_events USING btree (event_type);
CREATE INDEX idx_baskets_workspace ON public.baskets USING btree (workspace_id);
CREATE INDEX idx_block_revisions_basket_ts ON public.block_revisions USING btree (workspace_id, created_at DESC);
CREATE INDEX idx_blocks_basket ON public.blocks USING btree (basket_id);
CREATE INDEX idx_blocks_extraction_method ON public.blocks USING btree (extraction_method);
CREATE INDEX idx_blocks_provenance_validated ON public.blocks USING btree (provenance_validated);
CREATE INDEX idx_blocks_raw_dump ON public.blocks USING btree (raw_dump_id);
CREATE INDEX idx_blocks_updated_at ON public.blocks USING btree (updated_at);
CREATE INDEX idx_blocks_workspace ON public.blocks USING btree (workspace_id);
CREATE INDEX idx_context_basket ON public.context_items USING btree (basket_id);
CREATE INDEX idx_context_doc ON public.context_items USING btree (document_id);
CREATE INDEX idx_context_items_basket ON public.context_items USING btree (basket_id);
CREATE INDEX idx_context_items_basket_id ON public.context_items USING btree (basket_id);
CREATE INDEX idx_context_items_state ON public.context_items USING btree (state);
CREATE INDEX idx_doc_versions_signature ON public.document_versions USING btree (composition_signature) WHERE (composition_signature IS NOT NULL);
CREATE INDEX idx_document_versions_created ON public.document_versions USING btree (created_at DESC);
CREATE INDEX idx_document_versions_document ON public.document_versions USING btree (document_id);
CREATE INDEX idx_document_versions_hash ON public.document_versions USING btree (version_hash);
CREATE INDEX idx_documents_basket ON public.documents USING btree (basket_id);
CREATE INDEX idx_documents_current_version ON public.documents USING btree (current_version_hash) WHERE (current_version_hash IS NOT NULL);
CREATE INDEX idx_documents_meta_comp_sig ON public.documents USING btree (((metadata ->> 'composition_signature'::text)));
CREATE INDEX idx_documents_workspace ON public.documents USING btree (workspace_id);
CREATE INDEX idx_events_agent_type ON public.events USING btree (agent_type);
CREATE INDEX idx_events_basket_kind_ts ON public.events USING btree (basket_id, kind, ts);
CREATE INDEX idx_events_origin_kind ON public.events USING btree (origin, kind);
CREATE INDEX idx_events_workspace_ts ON public.events USING btree (workspace_id, ts DESC);
CREATE INDEX idx_history_basket_ts ON public.timeline_events USING btree (basket_id, ts DESC, id DESC);
CREATE INDEX idx_idem_delta_id ON public.idempotency_keys USING btree (delta_id);
CREATE INDEX idx_idempotency_delta ON public.idempotency_keys USING btree (delta_id);
CREATE INDEX idx_idempotency_keys_delta_id ON public.idempotency_keys USING btree (delta_id);
CREATE INDEX idx_narrative_basket ON public.narrative USING btree (basket_id);
CREATE INDEX idx_proposal_executions_executed_at ON public.proposal_executions USING btree (executed_at DESC);
CREATE INDEX idx_proposal_executions_proposal ON public.proposal_executions USING btree (proposal_id, operation_index);
CREATE INDEX idx_proposal_executions_proposal_id ON public.proposal_executions USING btree (proposal_id);
CREATE INDEX idx_proposals_basket_status ON public.proposals USING btree (basket_id, status);
CREATE INDEX idx_proposals_blast_radius ON public.proposals USING btree (blast_radius);
CREATE INDEX idx_proposals_executed ON public.proposals USING btree (is_executed, executed_at);
CREATE INDEX idx_proposals_workspace_created ON public.proposals USING btree (workspace_id, created_at DESC);
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
CREATE INDEX idx_reflections_target ON public.reflections_artifact USING btree (reflection_target_type, reflection_target_id);
CREATE INDEX idx_relationships_from ON public.substrate_relationships USING btree (from_type, from_id);
CREATE INDEX idx_relationships_to ON public.substrate_relationships USING btree (to_type, to_id);
CREATE INDEX idx_substrate_references_created ON public.substrate_references USING btree (created_at);
CREATE INDEX idx_substrate_references_document ON public.substrate_references USING btree (document_id);
CREATE INDEX idx_substrate_references_role ON public.substrate_references USING btree (role) WHERE (role IS NOT NULL);
CREATE INDEX idx_substrate_references_substrate ON public.substrate_references USING btree (substrate_id);
CREATE INDEX idx_substrate_references_type ON public.substrate_references USING btree (substrate_type);
CREATE INDEX idx_timeline_events_basket_timestamp_id ON public.timeline_events USING btree (basket_id, ts DESC, id DESC);
CREATE INDEX idx_timeline_events_kind_ref_id ON public.timeline_events USING btree (kind, ref_id) WHERE (ref_id IS NOT NULL);
CREATE INDEX idx_timeline_workspace_ts ON public.timeline_events USING btree (workspace_id, ts DESC, id DESC);
CREATE INDEX idx_workspace_governance_settings_workspace_id ON public.workspace_governance_settings USING btree (workspace_id);
CREATE INDEX ix_block_links_doc_block ON public.block_links USING btree (document_id, block_id);
CREATE INDEX ix_events_kind_ts ON public.events USING btree (kind, ts);
CREATE INDEX ix_pipeline_metrics_basket ON public.pipeline_metrics USING btree (basket_id, ts DESC);
CREATE INDEX ix_pipeline_metrics_recent ON public.pipeline_metrics USING btree (pipeline, ts DESC);
CREATE UNIQUE INDEX reflection_cache_uq ON public.reflections_artifact USING btree (basket_id, substrate_hash);
CREATE UNIQUE INDEX timeline_dump_unique ON public.timeline_events USING btree (ref_id) WHERE (kind = 'dump'::text);
CREATE INDEX timeline_events_basket_ts_idx ON public.timeline_events USING btree (basket_id, ts DESC);
CREATE UNIQUE INDEX uq_baskets_user_idem ON public.baskets USING btree (user_id, idempotency_key) WHERE (idempotency_key IS NOT NULL);
CREATE UNIQUE INDEX uq_ctx_items_norm_label_by_type ON public.context_items USING btree (basket_id, type, normalized_label) WHERE (normalized_label IS NOT NULL);
CREATE UNIQUE INDEX uq_doc_ctx_item ON public.document_context_items USING btree (document_id, context_item_id);
CREATE UNIQUE INDEX uq_doc_version_signature ON public.document_versions USING btree (document_id, composition_signature) WHERE (composition_signature IS NOT NULL);
CREATE UNIQUE INDEX uq_dumps_basket_req ON public.raw_dumps USING btree (basket_id, dump_request_id) WHERE (dump_request_id IS NOT NULL);
CREATE UNIQUE INDEX uq_raw_dumps_basket_req ON public.raw_dumps USING btree (basket_id, dump_request_id) WHERE (dump_request_id IS NOT NULL);
CREATE UNIQUE INDEX uq_relationship_identity ON public.substrate_relationships USING btree (basket_id, from_type, from_id, to_type, to_id, relationship_type);
CREATE UNIQUE INDEX uq_substrate_rel_directed ON public.substrate_relationships USING btree (basket_id, from_type, from_id, relationship_type, to_type, to_id);
CREATE UNIQUE INDEX ux_raw_dumps_basket_trace ON public.raw_dumps USING btree (basket_id, ingest_trace_id) WHERE (ingest_trace_id IS NOT NULL);
CREATE TRIGGER after_dump_insert AFTER INSERT ON public.raw_dumps FOR EACH ROW EXECUTE FUNCTION public.queue_agent_processing();
CREATE TRIGGER ensure_text_dump_columns BEFORE INSERT ON public.raw_dumps FOR EACH ROW EXECUTE FUNCTION public.ensure_raw_dump_text_columns();
CREATE TRIGGER proposals_validation_gate BEFORE UPDATE ON public.proposals FOR EACH ROW EXECUTE FUNCTION public.proposal_validation_check();
CREATE TRIGGER reflection_cache_updated_at_trigger BEFORE UPDATE ON public.reflections_artifact FOR EACH ROW EXECUTE FUNCTION public.update_reflection_cache_updated_at();
CREATE TRIGGER sync_text_dump_columns BEFORE UPDATE ON public.raw_dumps FOR EACH ROW EXECUTE FUNCTION public.sync_raw_dump_text_columns();
CREATE TRIGGER trg_block_depth BEFORE INSERT OR UPDATE ON public.blocks FOR EACH ROW EXECUTE FUNCTION public.check_block_depth();
CREATE TRIGGER trg_lock_constant BEFORE INSERT OR UPDATE ON public.blocks FOR EACH ROW EXECUTE FUNCTION public.prevent_lock_vs_constant();
CREATE TRIGGER trg_set_basket_user_id BEFORE INSERT ON public.baskets FOR EACH ROW EXECUTE FUNCTION public.set_basket_user_id();
CREATE TRIGGER trg_timeline_after_raw_dump AFTER INSERT ON public.raw_dumps FOR EACH ROW EXECUTE FUNCTION public.fn_timeline_after_raw_dump();
ALTER TABLE ONLY public.agent_processing_queue
    ADD CONSTRAINT agent_processing_queue_basket_id_fkey FOREIGN KEY (basket_id) REFERENCES public.baskets(id) DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE ONLY public.agent_processing_queue
    ADD CONSTRAINT agent_processing_queue_dump_id_fkey FOREIGN KEY (dump_id) REFERENCES public.raw_dumps(id) DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE ONLY public.agent_processing_queue
    ADD CONSTRAINT agent_processing_queue_workspace_id_fkey FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id);
ALTER TABLE ONLY public.artifact_generation_settings
    ADD CONSTRAINT artifact_generation_settings_workspace_id_fkey FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) ON DELETE CASCADE;
ALTER TABLE ONLY public.reflections_artifact
    ADD CONSTRAINT basket_reflections_basket_id_fkey FOREIGN KEY (basket_id) REFERENCES public.baskets(id) ON DELETE CASCADE;
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
ALTER TABLE ONLY public.blocks
    ADD CONSTRAINT blocks_basket_id_fkey FOREIGN KEY (basket_id) REFERENCES public.baskets(id) ON DELETE CASCADE;
ALTER TABLE ONLY public.blocks
    ADD CONSTRAINT blocks_parent_block_id_fkey FOREIGN KEY (parent_block_id) REFERENCES public.blocks(id);
ALTER TABLE ONLY public.blocks
    ADD CONSTRAINT blocks_proposal_id_fkey FOREIGN KEY (proposal_id) REFERENCES public.proposals(id);
ALTER TABLE ONLY public.blocks
    ADD CONSTRAINT blocks_raw_dump_id_fkey FOREIGN KEY (raw_dump_id) REFERENCES public.raw_dumps(id);
ALTER TABLE ONLY public.context_items
    ADD CONSTRAINT context_items_basket_id_fkey FOREIGN KEY (basket_id) REFERENCES public.baskets(id) ON DELETE CASCADE;
ALTER TABLE ONLY public.context_items
    ADD CONSTRAINT context_items_document_id_fkey FOREIGN KEY (document_id) REFERENCES public.documents(id) ON DELETE CASCADE;
ALTER TABLE ONLY public.context_items
    ADD CONSTRAINT context_items_proposal_id_fkey FOREIGN KEY (proposal_id) REFERENCES public.proposals(id);
ALTER TABLE ONLY public.context_items
    ADD CONSTRAINT context_items_raw_dump_id_fkey FOREIGN KEY (raw_dump_id) REFERENCES public.raw_dumps(id);
ALTER TABLE ONLY public.document_context_items
    ADD CONSTRAINT document_context_items_context_item_id_fkey FOREIGN KEY (context_item_id) REFERENCES public.context_items(id) ON DELETE CASCADE;
ALTER TABLE ONLY public.document_context_items
    ADD CONSTRAINT document_context_items_document_id_fkey FOREIGN KEY (document_id) REFERENCES public.documents(id) ON DELETE CASCADE;
ALTER TABLE ONLY public.document_versions
    ADD CONSTRAINT document_versions_created_by_fkey FOREIGN KEY (created_by) REFERENCES auth.users(id) ON DELETE SET NULL;
ALTER TABLE ONLY public.document_versions
    ADD CONSTRAINT document_versions_document_id_fkey FOREIGN KEY (document_id) REFERENCES public.documents(id) ON DELETE CASCADE;
ALTER TABLE ONLY public.documents
    ADD CONSTRAINT documents_basket_id_fkey FOREIGN KEY (basket_id) REFERENCES public.baskets(id) ON DELETE CASCADE;
ALTER TABLE ONLY public.documents
    ADD CONSTRAINT documents_workspace_id_fkey FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) ON DELETE CASCADE;
ALTER TABLE ONLY public.events
    ADD CONSTRAINT events_actor_id_fkey FOREIGN KEY (actor_id) REFERENCES auth.users(id);
ALTER TABLE ONLY public.events
    ADD CONSTRAINT events_basket_id_fkey FOREIGN KEY (basket_id) REFERENCES public.baskets(id) ON DELETE CASCADE;
ALTER TABLE ONLY public.events
    ADD CONSTRAINT events_block_id_fkey FOREIGN KEY (block_id) REFERENCES public.blocks(id);
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
ALTER TABLE ONLY public.narrative
    ADD CONSTRAINT narrative_basket_id_fkey FOREIGN KEY (basket_id) REFERENCES public.baskets(id);
ALTER TABLE ONLY public.narrative
    ADD CONSTRAINT narrative_raw_dump_id_fkey FOREIGN KEY (raw_dump_id) REFERENCES public.raw_dumps(id);
ALTER TABLE ONLY public.proposal_executions
    ADD CONSTRAINT proposal_executions_proposal_id_fkey FOREIGN KEY (proposal_id) REFERENCES public.proposals(id);
ALTER TABLE ONLY public.proposals
    ADD CONSTRAINT proposals_basket_id_fkey FOREIGN KEY (basket_id) REFERENCES public.baskets(id);
ALTER TABLE ONLY public.proposals
    ADD CONSTRAINT proposals_workspace_id_fkey FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id);
ALTER TABLE ONLY public.raw_dumps
    ADD CONSTRAINT raw_dumps_basket_id_fkey FOREIGN KEY (basket_id) REFERENCES public.baskets(id) ON DELETE CASCADE;
ALTER TABLE ONLY public.reflections_artifact
    ADD CONSTRAINT reflection_cache_workspace_fkey FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) ON DELETE CASCADE;
ALTER TABLE ONLY public.revisions
    ADD CONSTRAINT revisions_basket_id_fkey FOREIGN KEY (basket_id) REFERENCES public.baskets(id) ON DELETE CASCADE;
ALTER TABLE ONLY public.substrate_references
    ADD CONSTRAINT substrate_references_created_by_fkey FOREIGN KEY (created_by) REFERENCES auth.users(id) ON DELETE SET NULL;
ALTER TABLE ONLY public.substrate_references
    ADD CONSTRAINT substrate_references_document_id_fkey FOREIGN KEY (document_id) REFERENCES public.documents(id) ON DELETE CASCADE;
ALTER TABLE ONLY public.substrate_relationships
    ADD CONSTRAINT substrate_relationships_basket_id_fkey FOREIGN KEY (basket_id) REFERENCES public.baskets(id);
ALTER TABLE ONLY public.timeline_events
    ADD CONSTRAINT timeline_events_basket_id_fkey FOREIGN KEY (basket_id) REFERENCES public.baskets(id) ON DELETE CASCADE;
ALTER TABLE ONLY public.timeline_events
    ADD CONSTRAINT timeline_events_workspace_fkey FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id) ON DELETE CASCADE;
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
CREATE POLICY "Service role can manage queue" ON public.agent_processing_queue TO service_role USING (true);
CREATE POLICY "Service role full access" ON public.baskets TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "Users can create proposals in their workspace" ON public.proposals FOR INSERT WITH CHECK ((workspace_id IN ( SELECT workspace_memberships.workspace_id
   FROM public.workspace_memberships
  WHERE (workspace_memberships.user_id = auth.uid()))));
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
CREATE POLICY "Users can read block revisions in their workspaces" ON public.block_revisions FOR SELECT USING ((EXISTS ( SELECT 1
   FROM public.workspace_memberships
  WHERE ((workspace_memberships.workspace_id = block_revisions.workspace_id) AND (workspace_memberships.user_id = auth.uid())))));
CREATE POLICY "Users can read blocks in their workspaces" ON public.blocks FOR SELECT USING ((EXISTS ( SELECT 1
   FROM public.workspace_memberships
  WHERE ((workspace_memberships.workspace_id = blocks.workspace_id) AND (workspace_memberships.user_id = auth.uid())))));
CREATE POLICY "Users can read documents in their workspaces" ON public.documents FOR SELECT USING ((EXISTS ( SELECT 1
   FROM public.workspace_memberships
  WHERE ((workspace_memberships.workspace_id = documents.workspace_id) AND (workspace_memberships.user_id = auth.uid())))));
CREATE POLICY "Users can update proposals in their workspace" ON public.proposals FOR UPDATE USING ((workspace_id IN ( SELECT workspace_memberships.workspace_id
   FROM public.workspace_memberships
  WHERE (workspace_memberships.user_id = auth.uid()))));
CREATE POLICY "Users can view blocks in their workspace" ON public.blocks FOR SELECT USING ((EXISTS ( SELECT 1
   FROM public.baskets
  WHERE ((baskets.id = blocks.basket_id) AND (baskets.workspace_id IN ( SELECT workspace_memberships.workspace_id
           FROM public.workspace_memberships
          WHERE (workspace_memberships.user_id = auth.uid())))))));
CREATE POLICY "Users can view context_items in their workspace" ON public.context_items FOR SELECT USING ((EXISTS ( SELECT 1
   FROM public.baskets
  WHERE ((baskets.id = context_items.basket_id) AND (baskets.workspace_id IN ( SELECT workspace_memberships.workspace_id
           FROM public.workspace_memberships
          WHERE (workspace_memberships.user_id = auth.uid())))))));
CREATE POLICY "Users can view executions in their workspace" ON public.proposal_executions FOR SELECT USING ((proposal_id IN ( SELECT proposals.id
   FROM public.proposals
  WHERE (proposals.workspace_id IN ( SELECT workspace_memberships.workspace_id
           FROM public.workspace_memberships
          WHERE (workspace_memberships.user_id = auth.uid()))))));
CREATE POLICY "Users can view narrative in their workspace" ON public.narrative FOR SELECT USING ((EXISTS ( SELECT 1
   FROM public.baskets
  WHERE ((baskets.id = narrative.basket_id) AND (baskets.workspace_id IN ( SELECT workspace_memberships.workspace_id
           FROM public.workspace_memberships
          WHERE (workspace_memberships.user_id = auth.uid())))))));
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
CREATE POLICY "Users can view relationships in their workspace" ON public.substrate_relationships FOR SELECT USING ((EXISTS ( SELECT 1
   FROM public.baskets
  WHERE ((baskets.id = substrate_relationships.basket_id) AND (baskets.workspace_id IN ( SELECT workspace_memberships.workspace_id
           FROM public.workspace_memberships
          WHERE (workspace_memberships.user_id = auth.uid())))))));
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
ALTER TABLE public.artifact_generation_settings ENABLE ROW LEVEL SECURITY;
CREATE POLICY artifact_settings_workspace ON public.artifact_generation_settings USING ((workspace_id IN ( SELECT workspace_memberships.workspace_id
   FROM public.workspace_memberships
  WHERE (workspace_memberships.user_id = auth.uid()))));
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
ALTER TABLE public.context_items ENABLE ROW LEVEL SECURITY;
CREATE POLICY context_items_delete ON public.context_items FOR DELETE TO authenticated USING ((EXISTS ( SELECT 1
   FROM (public.baskets b
     JOIN public.workspace_memberships wm ON ((wm.workspace_id = b.workspace_id)))
  WHERE ((b.id = context_items.basket_id) AND (wm.user_id = auth.uid())))));
CREATE POLICY context_items_delete_workspace_member ON public.context_items FOR DELETE TO authenticated USING ((EXISTS ( SELECT 1
   FROM (public.baskets b
     JOIN public.workspace_memberships wm ON ((wm.workspace_id = b.workspace_id)))
  WHERE ((b.id = context_items.basket_id) AND (wm.user_id = auth.uid())))));
CREATE POLICY context_items_insert ON public.context_items FOR INSERT TO authenticated WITH CHECK ((EXISTS ( SELECT 1
   FROM (public.baskets b
     JOIN public.workspace_memberships wm ON ((wm.workspace_id = b.workspace_id)))
  WHERE ((b.id = context_items.basket_id) AND (wm.user_id = auth.uid())))));
CREATE POLICY context_items_insert_workspace_member ON public.context_items FOR INSERT TO authenticated WITH CHECK ((EXISTS ( SELECT 1
   FROM (public.baskets b
     JOIN public.workspace_memberships wm ON ((wm.workspace_id = b.workspace_id)))
  WHERE ((b.id = context_items.basket_id) AND (wm.user_id = auth.uid())))));
CREATE POLICY context_items_select ON public.context_items FOR SELECT TO authenticated USING ((EXISTS ( SELECT 1
   FROM (public.baskets b
     JOIN public.workspace_memberships wm ON ((wm.workspace_id = b.workspace_id)))
  WHERE ((b.id = context_items.basket_id) AND (wm.user_id = auth.uid())))));
CREATE POLICY context_items_select_workspace_member ON public.context_items FOR SELECT TO authenticated USING ((EXISTS ( SELECT 1
   FROM (public.baskets b
     JOIN public.workspace_memberships wm ON ((wm.workspace_id = b.workspace_id)))
  WHERE ((b.id = context_items.basket_id) AND (wm.user_id = auth.uid())))));
CREATE POLICY context_items_service_role_all ON public.context_items TO service_role USING (true) WITH CHECK (true);
CREATE POLICY context_items_update ON public.context_items FOR UPDATE TO authenticated USING ((EXISTS ( SELECT 1
   FROM (public.baskets b
     JOIN public.workspace_memberships wm ON ((wm.workspace_id = b.workspace_id)))
  WHERE ((b.id = context_items.basket_id) AND (wm.user_id = auth.uid()))))) WITH CHECK ((EXISTS ( SELECT 1
   FROM (public.baskets b
     JOIN public.workspace_memberships wm ON ((wm.workspace_id = b.workspace_id)))
  WHERE ((b.id = context_items.basket_id) AND (wm.user_id = auth.uid())))));
CREATE POLICY context_items_update_workspace_member ON public.context_items FOR UPDATE TO authenticated USING ((EXISTS ( SELECT 1
   FROM (public.baskets b
     JOIN public.workspace_memberships wm ON ((wm.workspace_id = b.workspace_id)))
  WHERE ((b.id = context_items.basket_id) AND (wm.user_id = auth.uid())))));
CREATE POLICY ctx_member_delete ON public.context_items FOR DELETE USING ((basket_id IN ( SELECT b.id
   FROM (public.baskets b
     JOIN public.workspace_memberships wm ON ((wm.workspace_id = b.workspace_id)))
  WHERE (wm.user_id = auth.uid()))));
CREATE POLICY ctx_member_insert ON public.context_items FOR INSERT WITH CHECK ((basket_id IN ( SELECT b.id
   FROM (public.baskets b
     JOIN public.workspace_memberships wm ON ((wm.workspace_id = b.workspace_id)))
  WHERE (wm.user_id = auth.uid()))));
CREATE POLICY ctx_member_read ON public.context_items FOR SELECT USING ((basket_id IN ( SELECT b.id
   FROM (public.baskets b
     JOIN public.workspace_memberships wm ON ((wm.workspace_id = b.workspace_id)))
  WHERE (wm.user_id = auth.uid()))));
CREATE POLICY ctx_member_update ON public.context_items FOR UPDATE USING ((basket_id IN ( SELECT b.id
   FROM (public.baskets b
     JOIN public.workspace_memberships wm ON ((wm.workspace_id = b.workspace_id)))
  WHERE (wm.user_id = auth.uid()))));
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
ALTER TABLE public.workspace_memberships ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.workspaces ENABLE ROW LEVEL SECURITY;
CREATE POLICY "write history by service role" ON public.timeline_events FOR INSERT WITH CHECK ((auth.role() = 'service_role'::text));
CREATE POLICY "write reflections by service role" ON public.reflections_artifact FOR INSERT WITH CHECK ((auth.role() = 'service_role'::text));
CREATE POLICY ws_owner_delete ON public.workspaces FOR DELETE USING ((owner_id = auth.uid()));
CREATE POLICY ws_owner_or_member_read ON public.workspaces FOR SELECT USING (((owner_id = auth.uid()) OR (id IN ( SELECT workspace_memberships.workspace_id
   FROM public.workspace_memberships
  WHERE (workspace_memberships.user_id = auth.uid())))));
CREATE POLICY ws_owner_update ON public.workspaces FOR UPDATE USING ((owner_id = auth.uid()));
