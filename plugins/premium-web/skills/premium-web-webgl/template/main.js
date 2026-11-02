// Wires the config to the stage, the point-morph scene and the shader field. Test flags: ?nogl ?rm ?slow ?field=ribbon
import { WEBGL_CONFIG as C } from './webgl.config.js';
import { init } from './src/stage.js';
import { FIRE, AURORA, COBALT } from './src/backdrop.js';
import { createPointMorph } from './src/point-morph.js';
import { createField } from './src/field.js';

const BACKDROPS = { fire: FIRE, aurora: AURORA, cobalt: COBALT };
const SLOW_BUDGET_MS = 1;                 // ?slow: force the governor to degrade, to prove the path works
const flags = new URLSearchParams(location.search);
const reduced = flags.has('rm') ? true : undefined;
const backdrop = typeof C.stage.backdrop === 'string' ? BACKDROPS[C.stage.backdrop] : C.stage.backdrop;

const stage = init(document.body, { ...C.stage, backdrop, reduced, zIndex: -1, budgetMs: flags.has('slow') ? SLOW_BUDGET_MS : C.stage.budgetMs });
stage.addScene(createPointMorph(C.pointMorph));
const fieldHost = document.querySelector('[data-field]');
const field = fieldHost ? createField(fieldHost, { ...C.field, kind: flags.get('field') || C.field.kind, reduced }) : null;
Object.assign(window, { stage, field });   // handles for the selftest and for the console
