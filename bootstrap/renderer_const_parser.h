#ifndef ELITE_RENDERER_CONST_PARSER_H
#define ELITE_RENDERER_CONST_PARSER_H
/* Pinned q_shared.c parser helpers read input but advance their char * cursor.
   Use a local pointer, never alias a const char ** as char **. If those helpers
   ever start writing input, this adapter must be revisited. */
static char *Switch_ParseExt(const char **cursor, qboolean allow_line_breaks)
{
    char *local = (char *)*cursor;
    char *token = COM_ParseExt(&local, allow_line_breaks);
    *cursor = local;
    return token;
}
static qboolean Switch_SkipBracedSection(const char **cursor, int depth)
{
    char *local = (char *)*cursor;
    qboolean result = SkipBracedSection(&local, depth);
    *cursor = local;
    return result;
}
static void Switch_SkipRestOfLine(const char **cursor)
{
    char *local = (char *)*cursor;
    SkipRestOfLine(&local);
    *cursor = local;
}
#endif
