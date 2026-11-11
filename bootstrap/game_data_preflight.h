#ifndef GAME_DATA_PREFLIGHT_H
#define GAME_DATA_PREFLIGHT_H
#define GAME_DATA_REQUIRED_PAKS 3
/* 0 means readable regular file; otherwise an errno value. Presence only. */
void GameData_Check(const char *base_dir, int status[GAME_DATA_REQUIRED_PAKS]);
#endif
