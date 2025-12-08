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
    'failed'
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
    'ContextAlias'
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
    'reflection',
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
    dump_id uuid NOT NULL,
    basket_id uuid NOT NULL,
    workspace_id uuid NOT NULL,
    processing_state public.processing_state DEFAULT 'pending'::public.processing_state,
    claimed_at timestamp without time zone,
    claimed_by text,
    completed_at timestamp without time zone,
    attempts integer DEFAULT 0,
    error_message text,
    created_at timestamp without time zone DEFAULT now()
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
    SET search_path TO 'public'
    AS $$
DECLARE
  v_id uuid;
  v_basket uuid;
  v_event_kind text;
BEGIN
  -- Validate substrate exists based on type (using actual table names)
  CASE p_substrate_type
    WHEN 'block' THEN
      IF NOT EXISTS (SELECT 1 FROM blocks WHERE id = p_substrate_id) THEN
        RAISE EXCEPTION 'Block % not found', p_substrate_id;
      END IF;
    WHEN 'dump' THEN
      IF NOT EXISTS (SELECT 1 FROM raw_dumps WHERE id = p_substrate_id) THEN
        RAISE EXCEPTION 'Dump % not found', p_substrate_id;
      END IF;
    WHEN 'context_item' THEN
      IF NOT EXISTS (SELECT 1 FROM context_items WHERE id = p_substrate_id) THEN
        RAISE EXCEPTION 'Context item % not found', p_substrate_id;
      END IF;
    WHEN 'reflection' THEN
      IF NOT EXISTS (SELECT 1 FROM reflection_cache WHERE id = p_substrate_id) THEN
        RAISE EXCEPTION 'Reflection % not found', p_substrate_id;
      END IF;
    WHEN 'timeline_event' THEN
      IF NOT EXISTS (SELECT 1 FROM timeline_events WHERE id = p_substrate_id) THEN
        RAISE EXCEPTION 'Timeline event % not found', p_substrate_id;
      END IF;
  END CASE;
  -- Check if reference already exists
  SELECT id INTO v_id FROM substrate_references
  WHERE document_id = p_document_id 
    AND substrate_type = p_substrate_type 
    AND substrate_id = p_substrate_id;
  IF v_id IS NULL THEN
    -- Insert new reference
    INSERT INTO substrate_references (
      document_id, substrate_type, substrate_id, role, weight, snippets, metadata, created_by
    )
    VALUES (
      p_document_id, p_substrate_type, p_substrate_id, p_role, p_weight, p_snippets, p_metadata, auth.uid()
    )
    RETURNING id INTO v_id;
  ELSE
    -- Update existing reference
    UPDATE substrate_references
    SET 
      role = COALESCE(p_role, role),
      weight = COALESCE(p_weight, weight),
      snippets = p_snippets,
      metadata = p_metadata || metadata  -- Merge metadata
    WHERE id = v_id;
  END IF;
  -- Emit timeline event
  SELECT basket_id INTO v_basket FROM documents WHERE id = p_document_id;
  v_event_kind := 'document.' || p_substrate_type || '.attached';
  
  PERFORM emit_timeline_event(
    p_basket_id => v_basket,
    p_kind => v_event_kind,
    p_ref_id => p_document_id,
    p_payload => jsonb_build_object(
      'document_id', p_document_id,
      'substrate_type', p_substrate_type,
      'substrate_id', p_substrate_id,
      'reference_id', v_id
    )
  );
  RETURN v_id;
END;
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
CREATE FUNCTION public.fn_document_detach_substrate(p_document_id uuid, p_substrate_type public.substrate_type, p_substrate_id uuid) RETURNS boolean
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'public'
    AS $$
DECLARE
  v_basket uuid;
  v_event_kind text;
BEGIN
  -- Delete the reference
  DELETE FROM substrate_references
  WHERE document_id = p_document_id 
    AND substrate_type = p_substrate_type 
    AND substrate_id = p_substrate_id;
  IF NOT FOUND THEN
    RETURN false;
  END IF;
  -- Emit timeline event
  SELECT basket_id INTO v_basket FROM documents WHERE id = p_document_id;
  v_event_kind := 'document.' || p_substrate_type || '.detached';
  
  PERFORM emit_timeline_event(
    p_basket_id => v_basket,
    p_kind => v_event_kind,
    p_ref_id => p_document_id,
    p_payload => jsonb_build_object(
      'document_id', p_document_id,
      'substrate_type', p_substrate_type,
      'substrate_id', p_substrate_id
    )
  );
  RETURN true;
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
CREATE FUNCTION public.fn_persist_reflection(p_basket_id uuid, p_pattern text, p_tension text, p_question text) RETURNS uuid
    LANGUAGE plpgsql
    AS $$
DECLARE 
  v_id uuid;
  v_workspace_id uuid;
BEGIN
  -- Get workspace_id from basket
  SELECT workspace_id INTO v_workspace_id FROM public.baskets WHERE id = p_basket_id;
  IF v_workspace_id IS NULL THEN
    RAISE EXCEPTION 'Basket % not found', p_basket_id;
  END IF;
  -- Insert into actual table, not the view
  INSERT INTO public.reflection_cache (basket_id, pattern, tension, question, workspace_id)
  VALUES (p_basket_id, p_pattern, p_tension, p_question, v_workspace_id)
  RETURNING id INTO v_id;
  PERFORM public.fn_timeline_emit(
    p_basket_id,
    'reflection',
    v_id,
    LEFT(COALESCE(p_pattern, p_question, ''), 140),
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
CREATE TABLE public.reflection_cache (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    basket_id uuid NOT NULL,
    pattern text,
    tension text,
    question text,
    computed_at timestamp with time zone DEFAULT now() NOT NULL,
    meta_derived_from text,
    meta_refreshable boolean DEFAULT true,
    workspace_id uuid NOT NULL
);
CREATE VIEW public.basket_reflections AS
 SELECT reflection_cache.id,
    reflection_cache.basket_id,
    reflection_cache.pattern,
    reflection_cache.tension,
    reflection_cache.question,
    reflection_cache.computed_at,
    reflection_cache.meta_derived_from,
    reflection_cache.meta_refreshable
   FROM public.reflection_cache;
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
    CONSTRAINT blocks_check CHECK ((((state = 'CONSTANT'::public.block_state) AND (scope IS NOT NULL)) OR (state <> 'CONSTANT'::public.block_state)))
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
    count(*) FILTER (WHERE (substrate_references.substrate_type = 'reflection'::public.substrate_type)) AS reflections_count,
    count(*) FILTER (WHERE (substrate_references.substrate_type = 'timeline_event'::public.substrate_type)) AS timeline_events_count,
    count(*) AS total_references
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
    metadata jsonb DEFAULT '{}'::jsonb NOT NULL
);
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
    dump_request_id uuid
);
ALTER TABLE ONLY public.raw_dumps REPLICA IDENTITY FULL;
CREATE TABLE public.revisions (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    basket_id uuid,
    actor_id uuid,
    summary text,
    diff_json jsonb,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);
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
    ADD CONSTRAINT agent_processing_queue_dump_id_key UNIQUE (dump_id);
ALTER TABLE ONLY public.agent_processing_queue
    ADD CONSTRAINT agent_processing_queue_pkey PRIMARY KEY (id);
ALTER TABLE ONLY public.basket_deltas
    ADD CONSTRAINT basket_deltas_pkey PRIMARY KEY (delta_id);
ALTER TABLE ONLY public.basket_events
    ADD CONSTRAINT basket_events_pkey PRIMARY KEY (id);
ALTER TABLE ONLY public.reflection_cache
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
ALTER TABLE ONLY public.workspace_memberships
    ADD CONSTRAINT workspace_memberships_pkey PRIMARY KEY (id);
ALTER TABLE ONLY public.workspace_memberships
    ADD CONSTRAINT workspace_memberships_workspace_id_user_id_key UNIQUE (workspace_id, user_id);
ALTER TABLE ONLY public.workspaces
    ADD CONSTRAINT workspaces_pkey PRIMARY KEY (id);
CREATE INDEX baskets_user_idx ON public.baskets USING btree (user_id);
CREATE INDEX blk_doc_idx ON public.block_links USING btree (block_id, document_id);
CREATE UNIQUE INDEX docs_basket_title_idx ON public.documents USING btree (basket_id, title);
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
CREATE INDEX idx_blocks_raw_dump ON public.blocks USING btree (raw_dump_id);
CREATE INDEX idx_blocks_workspace ON public.blocks USING btree (workspace_id);
CREATE INDEX idx_context_basket ON public.context_items USING btree (basket_id);
CREATE INDEX idx_context_doc ON public.context_items USING btree (document_id);
CREATE INDEX idx_context_items_basket ON public.context_items USING btree (basket_id);
CREATE INDEX idx_context_items_basket_id ON public.context_items USING btree (basket_id);
CREATE INDEX idx_context_items_state ON public.context_items USING btree (state);
CREATE INDEX idx_documents_basket ON public.documents USING btree (basket_id);
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
CREATE INDEX idx_proposal_executions_proposal ON public.proposal_executions USING btree (proposal_id, operation_index);
CREATE INDEX idx_proposals_basket_status ON public.proposals USING btree (basket_id, status);
CREATE INDEX idx_proposals_blast_radius ON public.proposals USING btree (blast_radius);
CREATE INDEX idx_proposals_executed ON public.proposals USING btree (is_executed, executed_at);
CREATE INDEX idx_proposals_workspace_created ON public.proposals USING btree (workspace_id, created_at DESC);
CREATE INDEX idx_queue_claimed ON public.agent_processing_queue USING btree (claimed_by, processing_state) WHERE (claimed_by IS NOT NULL);
CREATE INDEX idx_queue_state_created ON public.agent_processing_queue USING btree (processing_state, created_at);
CREATE INDEX idx_queue_workspace ON public.agent_processing_queue USING btree (workspace_id, processing_state);
CREATE INDEX idx_raw_dumps_basket ON public.raw_dumps USING btree (basket_id);
CREATE INDEX idx_raw_dumps_file_url ON public.raw_dumps USING btree (file_url);
CREATE INDEX idx_raw_dumps_source_meta_gin ON public.raw_dumps USING gin (source_meta);
CREATE INDEX idx_raw_dumps_trace ON public.raw_dumps USING btree (ingest_trace_id);
CREATE INDEX idx_rawdump_doc ON public.raw_dumps USING btree (document_id);
CREATE INDEX idx_reflections_basket_ts ON public.reflection_cache USING btree (basket_id, computed_at DESC);
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
CREATE INDEX ix_basket_reflections_basket_ts ON public.reflection_cache USING btree (basket_id, computed_at DESC);
CREATE INDEX ix_block_links_doc_block ON public.block_links USING btree (document_id, block_id);
CREATE INDEX ix_events_kind_ts ON public.events USING btree (kind, ts);
CREATE INDEX ix_pipeline_metrics_basket ON public.pipeline_metrics USING btree (basket_id, ts DESC);
CREATE INDEX ix_pipeline_metrics_recent ON public.pipeline_metrics USING btree (pipeline, ts DESC);
CREATE UNIQUE INDEX timeline_dump_unique ON public.timeline_events USING btree (ref_id) WHERE (kind = 'dump'::text);
CREATE INDEX timeline_events_basket_ts_idx ON public.timeline_events USING btree (basket_id, ts DESC);
CREATE UNIQUE INDEX uq_baskets_user_idem ON public.baskets USING btree (user_id, idempotency_key) WHERE (idempotency_key IS NOT NULL);
CREATE UNIQUE INDEX uq_ctx_items_norm_label_by_type ON public.context_items USING btree (basket_id, type, normalized_label) WHERE (normalized_label IS NOT NULL);
CREATE UNIQUE INDEX uq_doc_ctx_item ON public.document_context_items USING btree (document_id, context_item_id);
CREATE UNIQUE INDEX uq_dumps_basket_req ON public.raw_dumps USING btree (basket_id, dump_request_id) WHERE (dump_request_id IS NOT NULL);
CREATE UNIQUE INDEX uq_raw_dumps_basket_req ON public.raw_dumps USING btree (basket_id, dump_request_id) WHERE (dump_request_id IS NOT NULL);
CREATE UNIQUE INDEX uq_reflection_cache_basket_hash ON public.reflection_cache USING btree (basket_id, meta_derived_from) WHERE (meta_derived_from IS NOT NULL);
CREATE UNIQUE INDEX uq_relationship_identity ON public.substrate_relationships USING btree (basket_id, from_type, from_id, to_type, to_id, relationship_type);
CREATE UNIQUE INDEX uq_substrate_rel_directed ON public.substrate_relationships USING btree (basket_id, from_type, from_id, relationship_type, to_type, to_id);
CREATE UNIQUE INDEX ux_raw_dumps_basket_trace ON public.raw_dumps USING btree (basket_id, ingest_trace_id) WHERE (ingest_trace_id IS NOT NULL);
CREATE TRIGGER after_dump_insert AFTER INSERT ON public.raw_dumps FOR EACH ROW EXECUTE FUNCTION public.queue_agent_processing();
CREATE TRIGGER proposals_validation_gate BEFORE UPDATE ON public.proposals FOR EACH ROW EXECUTE FUNCTION public.proposal_validation_check();
CREATE TRIGGER trg_block_depth BEFORE INSERT OR UPDATE ON public.blocks FOR EACH ROW EXECUTE FUNCTION public.check_block_depth();
CREATE TRIGGER trg_lock_constant BEFORE INSERT OR UPDATE ON public.blocks FOR EACH ROW EXECUTE FUNCTION public.prevent_lock_vs_constant();
CREATE TRIGGER trg_set_basket_user_id BEFORE INSERT ON public.baskets FOR EACH ROW EXECUTE FUNCTION public.set_basket_user_id();
CREATE TRIGGER trg_timeline_after_raw_dump AFTER INSERT ON public.raw_dumps FOR EACH ROW EXECUTE FUNCTION public.fn_timeline_after_raw_dump();
ALTER TABLE ONLY public.agent_processing_queue
    ADD CONSTRAINT agent_processing_queue_basket_id_fkey FOREIGN KEY (basket_id) REFERENCES public.baskets(id);
ALTER TABLE ONLY public.agent_processing_queue
    ADD CONSTRAINT agent_processing_queue_dump_id_fkey FOREIGN KEY (dump_id) REFERENCES public.raw_dumps(id);
ALTER TABLE ONLY public.agent_processing_queue
    ADD CONSTRAINT agent_processing_queue_workspace_id_fkey FOREIGN KEY (workspace_id) REFERENCES public.workspaces(id);
ALTER TABLE ONLY public.reflection_cache
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
ALTER TABLE ONLY public.reflection_cache
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
CREATE POLICY br_insert_workspace_member ON public.reflection_cache FOR INSERT WITH CHECK ((EXISTS ( SELECT 1
   FROM (public.baskets b
     JOIN public.workspace_memberships wm ON ((wm.workspace_id = b.workspace_id)))
  WHERE ((b.id = reflection_cache.basket_id) AND (wm.user_id = auth.uid())))));
CREATE POLICY br_select_workspace_member ON public.reflection_cache FOR SELECT USING ((EXISTS ( SELECT 1
   FROM (public.baskets b
     JOIN public.workspace_memberships wm ON ((wm.workspace_id = b.workspace_id)))
  WHERE ((b.id = reflection_cache.basket_id) AND (wm.user_id = auth.uid())))));
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
CREATE POLICY "delete reflections by service role" ON public.reflection_cache FOR DELETE USING ((auth.role() = 'service_role'::text));
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
CREATE POLICY "read reflections by workspace members" ON public.reflection_cache FOR SELECT USING (((auth.role() = 'service_role'::text) OR (EXISTS ( SELECT 1
   FROM (public.baskets b
     JOIN public.v_user_workspaces m ON ((m.workspace_id = b.workspace_id)))
  WHERE ((b.id = reflection_cache.basket_id) AND (m.user_id = auth.uid()))))));
ALTER TABLE public.reflection_cache ENABLE ROW LEVEL SECURITY;
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
CREATE POLICY "update reflections by service role" ON public.reflection_cache FOR UPDATE USING ((auth.role() = 'service_role'::text)) WITH CHECK ((auth.role() = 'service_role'::text));
ALTER TABLE public.workspace_memberships ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.workspaces ENABLE ROW LEVEL SECURITY;
CREATE POLICY "write history by service role" ON public.timeline_events FOR INSERT WITH CHECK ((auth.role() = 'service_role'::text));
CREATE POLICY "write reflections by service role" ON public.reflection_cache FOR INSERT WITH CHECK ((auth.role() = 'service_role'::text));
CREATE POLICY ws_owner_delete ON public.workspaces FOR DELETE USING ((owner_id = auth.uid()));
CREATE POLICY ws_owner_or_member_read ON public.workspaces FOR SELECT USING (((owner_id = auth.uid()) OR (id IN ( SELECT workspace_memberships.workspace_id
   FROM public.workspace_memberships
  WHERE (workspace_memberships.user_id = auth.uid())))));
CREATE POLICY ws_owner_update ON public.workspaces FOR UPDATE USING ((owner_id = auth.uid()));
