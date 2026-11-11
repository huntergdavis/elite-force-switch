#ifndef ELITE_SWITCH_UI_MEDIA_H
#define ELITE_SWITCH_UI_MEDIA_H

/* The registry must live as long as the retained UI.
 * No engine handle is cached: consumers resolve the copied name against the
 * current renderer/sound registry. Calls are single-threaded and non-reentrant.
 * Bridge wrappers install the registry alongside the UI suspend/resume path. */
#include <stddef.h>
#include <string.h>

enum class ResidentMediaKind { Model, Skin, Shader, ShaderNoMip, Sound };
enum class ResidentMediaUse { Model, Skin, Shader, Sound };
enum class ResidentMediaError { InvalidName, InvalidKind, Full, InvalidHandle,
                                WrongKind, MissingBackend };
typedef int (*ResidentMediaRegister)(void *, ResidentMediaKind, const char *);
typedef void (*ResidentMediaReport)(void *, ResidentMediaError);

template<size_t Capacity = 4096, size_t NameCapacity = 64>
class ResidentUiMedia {
    static_assert(Capacity > 0 && Capacity <= 0x7fffffff, "IDs must fit positive int");
    static_assert(NameCapacity > 1, "resource names need a terminator");
    struct Entry { ResidentMediaKind kind; char name[NameCapacity]; };
    Entry entries_[Capacity] = {};
    size_t count_ = 0;
    void *context_;
    ResidentMediaRegister register_;
    ResidentMediaReport report_;

    int Reject(ResidentMediaError error) const {
        if (report_) report_(context_, error);
        return 0;
    }
    static bool ValidKind(ResidentMediaKind kind) {
        switch (kind) {
        case ResidentMediaKind::Model: case ResidentMediaKind::Skin:
        case ResidentMediaKind::Shader: case ResidentMediaKind::ShaderNoMip:
        case ResidentMediaKind::Sound: return true;
        }
        return false;
    }
    static bool Accepts(ResidentMediaUse use, ResidentMediaKind kind) {
        switch (use) {
        case ResidentMediaUse::Model: return kind == ResidentMediaKind::Model;
        case ResidentMediaUse::Skin: return kind == ResidentMediaKind::Skin;
        case ResidentMediaUse::Shader:
            return kind == ResidentMediaKind::Shader || kind == ResidentMediaKind::ShaderNoMip;
        case ResidentMediaUse::Sound: return kind == ResidentMediaKind::Sound;
        }
        return false;
    }

public:
    ResidentUiMedia(void *context, ResidentMediaRegister registration,
                    ResidentMediaReport report = nullptr)
        : context_(context), register_(registration), report_(report) {}

    size_t Size() const { return count_; }

    int Register(ResidentMediaKind kind, const char *name) {
        if (!ValidKind(kind)) return Reject(ResidentMediaError::InvalidKind);
        if (!register_) return Reject(ResidentMediaError::MissingBackend);
        if (!name || !name[0]) return Reject(ResidentMediaError::InvalidName);
        size_t length = 0;
        while (length < NameCapacity && name[length]) ++length;
        if (length == NameCapacity) return Reject(ResidentMediaError::InvalidName);
        for (size_t i = 0; i < count_; ++i) {
            const Entry &entry = entries_[i];
            if (entry.kind == kind && strcmp(entry.name, name) == 0) {
                const int actual = register_(context_, kind, entry.name);
                return actual > 0 ? static_cast<int>(i + 1) : actual;
            }
        }
        if (count_ == Capacity) return Reject(ResidentMediaError::Full);
        /* Copy before calling the backend; callers may supply mutable buffers. */
        char saved_name[NameCapacity];
        memcpy(saved_name, name, length + 1);
        const int actual = register_(context_, kind, saved_name);
        if (actual <= 0) return actual; // preserve the backend's failure result
        Entry &entry = entries_[count_];
        entry.kind = kind;
        memcpy(entry.name, saved_name, length + 1);
        ++count_;
        return static_cast<int>(count_);
    }

    int Resolve(ResidentMediaUse use, int proxy) const {
        if (proxy <= 0) return proxy; // shader 0/default and sound -1/no-sound
        if (static_cast<size_t>(proxy) > count_)
            return Reject(ResidentMediaError::InvalidHandle);
        const Entry &entry = entries_[static_cast<size_t>(proxy) - 1];
        if (!Accepts(use, entry.kind)) return Reject(ResidentMediaError::WrongKind);
        if (!register_) return Reject(ResidentMediaError::MissingBackend);
        return register_(context_, entry.kind, entry.name);
    }

    template<typename Entity>
    Entity TranslateEntity(const Entity &source) const {
        Entity translated = source;
        translated.hModel = Resolve(ResidentMediaUse::Model, source.hModel);
        translated.customSkin = Resolve(ResidentMediaUse::Skin, source.customSkin);
        translated.customShader = Resolve(ResidentMediaUse::Shader, source.customShader);
        return translated;
    }
};
#endif
