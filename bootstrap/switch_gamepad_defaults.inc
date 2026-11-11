/* Called once after user configuration is read; existing nonempty binds win. */
#ifdef __SWITCH__
extern int Key_StringToKeynum(char *name);
extern char *Key_GetBinding(int keynum);
extern void Key_SetBinding(int keynum, const char *binding);
static void Switch_InstallGamepadDefaults(void) {
    static const struct { const char *key, *command; } defaults[] = {
        {"PAD0_LEFTSTICK_UP", "+forward"}, {"PAD0_LEFTSTICK_DOWN", "+back"},
        {"PAD0_LEFTSTICK_LEFT", "+moveleft"}, {"PAD0_LEFTSTICK_RIGHT", "+moveright"},
        {"PAD0_RIGHTSTICK_UP", "+lookup"}, {"PAD0_RIGHTSTICK_DOWN", "+lookdown"},
        {"PAD0_RIGHTSTICK_LEFT", "+left"}, {"PAD0_RIGHTSTICK_RIGHT", "+right"},
        {"PAD0_RIGHTTRIGGER", "+attack"}, {"PAD0_LEFTTRIGGER", "+altattack"},
        {"PAD0_RIGHTSHOULDER", "weapnext"}, {"PAD0_LEFTSHOULDER", "weapprev"},
        {"PAD0_A", "+moveup"}, {"PAD0_B", "+movedown"}, {"PAD0_X", "+use"},
        {"PAD0_Y", "weapnext"}, {"PAD0_RIGHTSTICK_CLICK", "+zoom"},
        {"PAD0_DPAD_UP", "+button2"}, {"PAD0_DPAD_DOWN", "+button3"},
        {"PAD0_DPAD_LEFT", "weapprev"}, {"PAD0_DPAD_RIGHT", "weapnext"},
        {"PAD0_START", "togglemenu"}, {"PAD0_BACK", "+info"}
    };
    cvar_t *stamp = Cvar_Get("in_switchDefaults", "0", CVAR_ARCHIVE);
    if (stamp->integer >= 1) return;
    Cvar_Get("in_joystick", "1", CVAR_ARCHIVE | CVAR_LATCH);
    Cvar_Get("in_joystickUseAnalog", "1", CVAR_ARCHIVE);
    Cvar_Get("joy_threshold", "0.15", CVAR_ARCHIVE);
    Cvar_Get("j_forward", "-0.004", CVAR_ARCHIVE);
    Cvar_Get("j_side", "0.004", CVAR_ARCHIVE);
    Cvar_Get("j_pitch", "0.0055", CVAR_ARCHIVE);
    Cvar_Get("j_yaw", "-0.0075", CVAR_ARCHIVE);
    for (unsigned i = 0; i < sizeof(defaults) / sizeof(defaults[0]); ++i) {
        int key = Key_StringToKeynum((char *)defaults[i].key);
        char *binding = key < 0 ? NULL : Key_GetBinding(key);
        if (key >= 0 && (!binding || !*binding)) Key_SetBinding(key, defaults[i].command);
    }
    Cvar_Set("in_switchDefaults", "1");
}
#endif
