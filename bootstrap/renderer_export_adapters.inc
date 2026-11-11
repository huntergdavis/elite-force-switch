/* Typed experimental bridge from SP's public exports to renderervk internals. */
static void Switch_RE_Shutdown(qboolean value)
{
    /* Preserve upstream's numeric 0/1 interpretation; semantics remain unverified. */
    RE_Shutdown(value ? REF_KEEP_WINDOW : REF_KEEP_CONTEXT);
}

static void Switch_RE_AddRefEntityToScene(const refEntity_t *entity)
{
    RE_AddRefEntityToScene(entity, qfalse);
}

/* No temporary allocation is made: downstream renderer errors may longjmp.
   Cinematics are deliberately unavailable until ownership and recovery are solved. */
static void Switch_RE_StretchRaw(int x, int y, int w, int h, int cols, int rows,
                                 const byte *data, int client, qboolean dirty)
{
    (void)x; (void)y; (void)w; (void)h; (void)cols; (void)rows;
    (void)data; (void)client; (void)dirty;
    ri.Error(ERR_DROP, "Cinematic rendering is not supported in the Switch bootstrap");
}

static void Switch_RE_UploadCinematic(int w, int h, int cols, int rows,
                                      const byte *data, int client, qboolean dirty)
{
    (void)w; (void)h; (void)cols; (void)rows;
    (void)data; (void)client; (void)dirty;
    ri.Error(ERR_DROP, "Cinematic upload is not supported in the Switch bootstrap");
}
