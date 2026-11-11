/* VoyagerNX input does not implement SP's flexible-display cursor sync.
 * This build-stage boundary intentionally leaves the UI cursor unsynchronized;
 * port SP absolute mouse tracking before claiming menu input compatibility. */
void IN_SyncMousePosition(void)
{
}
