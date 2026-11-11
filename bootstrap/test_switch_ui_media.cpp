#include "switch_ui_media.h"
/* Exercise translation with the actual pinned SP entity layout. */
#include "q_shared.h"
#include "tr_types.h"
#include <assert.h>
#include <limits.h>
#include <stdio.h>

struct FakeEngine {
    struct Resource { ResidentMediaKind kind; char name[64]; int handle; } resources[32] = {};
    int generation = 1;
    size_t count = 0;
    unsigned calls = 0;
    unsigned errors = 0;
    ResidentMediaError last_error = ResidentMediaError::InvalidName;
    char last_name[64] = {};
    void Restart() { ++generation; count = 0; }
    static int Register(void *context, ResidentMediaKind kind, const char *name) {
        FakeEngine &engine = *static_cast<FakeEngine *>(context);
        ++engine.calls;
        strcpy(engine.last_name, name);
        if (strcmp(name, "missing") == 0) return 0;
        if (strcmp(name, "negative") == 0) return -1;
        for (size_t i = 0; i < engine.count; ++i) {
            const Resource &resource = engine.resources[i];
            if (resource.kind == kind && strcmp(resource.name, name) == 0)
                return resource.handle;
        }
        assert(engine.count < 32);
        Resource &resource = engine.resources[engine.count++];
        resource.kind = kind;
        strcpy(resource.name, name);
        resource.handle = engine.generation * 1000 + static_cast<int>(engine.count);
        return resource.handle;
    }
    static void Report(void *context, ResidentMediaError error) {
        FakeEngine &engine = *static_cast<FakeEngine *>(context);
        ++engine.errors;
        engine.last_error = error;
    }
};

static void TestRefreshAndEntity() {
    FakeEngine engine;
    ResidentUiMedia<16> media(&engine, FakeEngine::Register, FakeEngine::Report);
    const int model = media.Register(ResidentMediaKind::Model, "models/player.md3");
    const int skin = media.Register(ResidentMediaKind::Skin, "models/player.skin");
    char shader_name[] = "menu/button";
    const int shader = media.Register(ResidentMediaKind::Shader, shader_name);
    const int nomip = media.Register(ResidentMediaKind::ShaderNoMip, "menu/button");
    const int sound = media.Register(ResidentMediaKind::Sound, "sound/click.wav");
    assert(model > 0 && skin > 0 && shader > 0 && nomip > 0 && sound > 0);
    assert(shader != nomip);
    assert(media.Register(ResidentMediaKind::Shader, shader_name) == shader);
    assert(media.Size() == 5);
    shader_name[0] = 'X';
    const int old_shader = media.Resolve(ResidentMediaUse::Shader, shader);
    assert(strcmp(engine.last_name, "menu/button") == 0); // owns its copied name
    const int old_nomip = media.Resolve(ResidentMediaUse::Shader, nomip);
    const int old_sound = media.Resolve(ResidentMediaUse::Sound, sound);

    refEntity_t source = {};
    source.reType = RT_MODEL;
    source.hModel = model;
    source.customSkin = skin;
    source.customShader = shader;
    source.skinNum = 7; // inline skin index, must not be translated
    source.frame = 9;
    source.origin[0] = 1.25f;
    source.origin[1] = -2.5f;
    source.shaderRGBA[0] = 187;
    const refEntity_t before = source;
    const refEntity_t old_entity = media.TranslateEntity(source);
    assert(old_entity.hModel > 1000 && old_entity.customSkin > 1000);

    for (int restart = 0; restart < 3; ++restart) {
        engine.Restart();
        const int current_shader = media.Resolve(ResidentMediaUse::Shader, shader);
        const int current_nomip = media.Resolve(ResidentMediaUse::Shader, nomip);
        const int current_sound = media.Resolve(ResidentMediaUse::Sound, sound);
        assert(current_shader != old_shader && current_nomip != old_nomip);
        assert(current_sound != old_sound);
        assert(current_shader / 1000 == engine.generation);
        assert(current_sound / 1000 == engine.generation);
        const refEntity_t translated = media.TranslateEntity(source);
        assert(translated.hModel != old_entity.hModel);
        assert(translated.customSkin != old_entity.customSkin);
        assert(translated.customShader == current_shader);
        assert(translated.hModel / 1000 == engine.generation);
        assert(translated.customSkin / 1000 == engine.generation);
        refEntity_t expected = before;
        expected.hModel = translated.hModel;
        expected.customSkin = translated.customSkin;
        expected.customShader = translated.customShader;
        assert(memcmp(&translated, &expected, sizeof(expected)) == 0);
        assert(memcmp(&source, &before, sizeof(source)) == 0);
        assert(media.Register(ResidentMediaKind::Shader, "menu/button") == shader);
        assert(media.Size() == 5);
    }
    // Tag interpolation uses the same Model resolver as entity model handles.
    assert(media.Resolve(ResidentMediaUse::Model, model) / 1000 == engine.generation);
    assert(media.Resolve(ResidentMediaUse::Skin, skin) / 1000 == engine.generation);
    const unsigned calls = engine.calls;
    assert(media.Resolve(ResidentMediaUse::Shader, 0) == 0);
    assert(media.Resolve(ResidentMediaUse::Sound, -1) == -1);
    assert(media.Resolve(ResidentMediaUse::Model, -7) == -7);
    assert(engine.calls == calls); // sentinels never invoke resource registration
    refEntity_t empty = {};
    const refEntity_t empty_translated = media.TranslateEntity(empty);
    assert(empty_translated.hModel == 0 && empty_translated.customSkin == 0);
    assert(empty_translated.customShader == 0 && engine.calls == calls);
    assert(engine.errors == 0);
}

static void TestFailuresAndBounds() {
    FakeEngine engine;
    ResidentUiMedia<2, 8> media(&engine, FakeEngine::Register, FakeEngine::Report);
    assert(media.Register(ResidentMediaKind::Shader, nullptr) == 0);
    assert(media.Register(ResidentMediaKind::Shader, "") == 0);
    assert(media.Register(ResidentMediaKind::Shader, "12345678") == 0);
    assert(media.Register(static_cast<ResidentMediaKind>(99), "ok") == 0);
    assert(engine.calls == 0 && media.Size() == 0);
    assert(media.Register(ResidentMediaKind::Shader, "missing") == 0);
    assert(media.Register(ResidentMediaKind::Sound, "negative") == 0); // too long for this table
    assert(media.Size() == 0);
    const int shader = media.Register(ResidentMediaKind::Shader, "1234567");
    const int sound = media.Register(ResidentMediaKind::Sound, "click");
    assert(shader == 1 && sound == 2);
    assert(media.Resolve(ResidentMediaUse::Model, shader) == 0);
    assert(engine.last_error == ResidentMediaError::WrongKind);
    assert(media.Resolve(ResidentMediaUse::Shader, sound) == 0);
    assert(media.Resolve(ResidentMediaUse::Shader, INT_MAX) == 0);
    assert(engine.last_error == ResidentMediaError::InvalidHandle);
    const unsigned calls = engine.calls;
    assert(media.Register(ResidentMediaKind::Model, "third") == 0);
    assert(engine.last_error == ResidentMediaError::Full && engine.calls == calls);
    assert(media.Register(ResidentMediaKind::Shader, "1234567") == shader);
    assert(media.Size() == 2); // known resources work after capacity is reached
    ResidentUiMedia<1> unconfigured(nullptr, nullptr);
    assert(unconfigured.Register(ResidentMediaKind::Shader, "valid") == 0);
    ResidentUiMedia<2> backend_failure(&engine, FakeEngine::Register);
    assert(backend_failure.Register(ResidentMediaKind::Sound, "negative") == -1);
    assert(backend_failure.Size() == 0);
}

int main() {
    TestRefreshAndEntity();
    TestFailuresAndBounds();
    puts("PASS: three media restarts, copied names, kind separation, actual SP entity translation, sentinels and bounds");
}
