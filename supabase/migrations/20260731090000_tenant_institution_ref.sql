-- =============================================================================
-- Vínculo tenant → namespace institucional del contenido curado
-- =============================================================================
-- El `id` de un tenant lo asigna la base; el identificador con el que se
-- publican el corpus documental (`domains/*/sources.yaml`) y la matriz de
-- permisos (`config/permissions.yaml`) lo asigna quien cura ese contenido.
-- Derivar el segundo del primero (`inst_{id}`) hacía que el retriever filtrara
-- por una institución inexistente: cero fragmentos recuperados, cero tools
-- visibles y ninguna regla de permisos aplicable — todo ello sin un solo error,
-- solo una respuesta «no encontré documentación vigente».
--
-- El vínculo pasa a ser explícito. `institution_ref()` en el backend lo lee y
-- conserva el fallback derivado para tenants que aún no lo declaren.
-- =============================================================================

update public.tenants
   set metadata = metadata || jsonb_build_object('institution_id', 'inst_demo')
 where slug = 'gobierno-demo'
   and metadata->>'institution_id' is distinct from 'inst_demo';
