/* PAL's sword trail (effect type 77) on the Japanese engine.
 *
 * Compiled hard-float (see b7_build_jp.py); odd FPU registers are kept free because the game's
 * code expects $f20-$f31 preserved across calls, not just the even ones n32 saves.
 *
 * PAL rewrote effect 77 (0x2d81f8 + strip helper 0x2d8120): instead of JP's single thin ribbon
 * off bone 29 (0x2dffc8), it keeps two edge histories of 6 frames x 4 points, picks the bone and
 * the blade shape from the character's state (combo 21, stab 22, and 4 / 41 for other wielders),
 * and draws each history as a fading strip.  This is that function, calling the JP equivalents of
 * every PAL routine it uses (same code in both builds, only the addresses moved).  It goes into
 * the JP effect program table at 0x433738[77]; JP's spawn sites already start it.
 */
typedef unsigned char u8;
typedef unsigned int u32;
typedef unsigned long long u64;

#define EFF_OBJ   0x5fa340          /* JP effect objects, 0x90 bytes each, 512 (PAL 0x61a020) */
#define VIEW_TBL  ((void *)0x433ae0) /* = PAL 0x43e160 */

#define alloc_     ((void *(*)(u32))0x2f2008)
#define memzero_   ((void (*)(void *, u32))0x2f936c)
#define free_      ((void (*)(void *))0x2f20e8)
#define bone_mtx   ((int (*)(void *, int, void *))0x3babe0)
#define mtx_view   ((void (*)(void *, void *, void *))0x391168)
#define vu_load    ((void (*)(void *))0x2f948c)
#define qmove      ((void (*)(void *, void *, int))0x394520)
#define vu_apply   ((void (*)(void *, void *, int))0x2f9f2c)
#define qcopy      ((void (*)(void *, void *, int))0x394340)
#define vu_xform   ((void (*)(void *, void *, void *, int))0x2f923c)
#define vu_sub     ((void (*)(void *, void *, void *))0x2f9268)
#define vu_mul     ((void (*)(void *, void *, void *))0x3c2958)
#define set_view   ((void (*)(void *))0x2f45a0)
#define gs_mode1   ((void (*)(int))0x2f7868)
#define gs_mode2   ((void (*)(int))0x2f7848)
#define to_screen  ((int (*)(void *, void *, int))0x2f9798)
#define draw_quad  ((void (*)(u64 *))0x2f7478)

#define A16 __attribute__((aligned(16)))

/* PAL 0x439470: per style, edge A (4 points) then edge B (4 points), bone-local */
static const float shape[4][2][16] A16 = {
  {{-0.15f,-0.25f,-0.2f,1, -0.15f,-0.05f,-0.2f,1, -0.15f,-0.25f,-0.4f,1, -0.15f,-0.05f,-0.4f,1},
   {-0.15f,-0.25f, 0.2f,1, -0.15f,-0.05f, 0.2f,1, -0.15f,-0.25f, 0.4f,1, -0.15f,-0.05f, 0.4f,1}},
  {{-0.38f,0.35f,-0.38f,1, -0.38f,0.15f,-0.38f,1, -0.48f,0.35f,-0.58f,1, -0.48f,0.15f,-0.58f,1},
   {-0.38f,0.35f, 0.38f,1, -0.38f,0.15f, 0.38f,1, -0.48f,0.35f, 0.58f,1, -0.48f,0.15f, 0.58f,1}},
  {{-0.8f,-0.2f,-0.2f,1, -0.8f,0.0f,-0.2f,1, -0.9f,-0.2f,-0.4f,1, -0.9f,0.0f,-0.4f,1},
   {-0.8f,-0.2f, 0.2f,1, -0.8f,0.0f, 0.2f,1, -0.9f,-0.2f, 0.4f,1, -0.9f,0.0f, 0.4f,1}},
  {{0.3f,0.2f,-0.2f,1, 0.3f,-0.2f,-0.2f,1, 0.3f,0.2f,-0.6f,1, 0.3f,-0.2f,-0.6f,1},
   {0.3f,0.2f, 0.2f,1, 0.3f,-0.2f, 0.2f,1, 0.3f,0.2f, 0.6f,1, 0.3f,-0.2f, 0.6f,1}},
};

static float bone[16] A16;     /* PAL sp+768 */
static float view[16] A16;     /* PAL sp+832 */
static float d[4] A16, sq[4] A16;
static float pts[48 * 4] A16;  /* PAL sp+0: both histories in view space */
static u64 quad[8] A16;        /* PAL sp+880: 4 colours, 4 screen vertices */
static u64 scr[2] A16;         /* PAL 0x525b30 */
static int clip;               /* PAL gp-12928 */
static u8 alpha;               /* PAL gp-12924 */

/* PAL 0x2d8120: next cross-section of the strip */
static void strip(void *p)
{
  int was = clip;
  u64 c;
  quad[0] = quad[2]; quad[1] = quad[2];
  c = (u64)alpha << 24 | 0xff;
  quad[2] = c; quad[3] = c;
  alpha = (u8)((alpha * 3) >> 2);
  quad[4] = scr[0]; quad[5] = scr[1];
  clip = to_screen(scr, p, 2);
  if (was == 0 && clip == 0) { quad[6] = scr[0]; quad[7] = scr[1]; draw_quad(quad); }
}

static void ribbon(float *p, int n)
{
  int i;
  for (i = 0; i <= n; i++, p += 16) {
    if (i == 0) { quad[2] = 0x800000ff; alpha = 0x80; clip = to_screen(scr, p, 2); }
    else strip(p);
    strip(p + 8);
  }
}

/* x+y+z < 2500.0 (PAL gp float 0x51a324) */
static int near(const float *v) { return v[0] + v[1] + v[2] < 2500.0f; }

void my_eff77(int slot, void **param)
{
  u8 *o = (u8 *)(EFF_OBJ + slot * 0x90);
  u8 *pl, *buf;
  int b, style, age;
  short st;

  if (*(short *)(o + 8) == 0) {
    buf = alloc_(0x300);
    *(void **)(o + 4) = buf;
    if (!buf) *(short *)(o + 8) = -1;
    else memzero_(buf, 0x300);
    return;
  }
  pl = (u8 *)param[0];
  st = *(short *)(pl + 388);
  if (st == 21) { b = 29; style = 0; }
  else if (st == 22) { b = 29; style = 1; }
  else if (st == 4) { b = 57; style = 2; }
  else if (st == 41) { b = 35; style = 3; }
  else { b = 0; style = -1; }
  age = *(int *)(o + 12);
  if (style < 0 || !((*(u32 *)(pl + 192) & 1) || age < 31) || !bone_mtx(pl, b, bone)) {
    free_(*(void **)(o + 4));
    *(short *)(o + 8) = -1;
    return;
  }
  buf = *(u8 **)(o + 4);
  mtx_view(view, bone, VIEW_TBL);
  vu_load(bone);
  qmove(buf + 0x40, buf, 20);
  vu_apply(buf, (void *)shape[style][0], 4);
  qmove(buf + 0x1c0, buf + 0x180, 20);
  vu_apply(buf + 0x180, (void *)shape[style][1], 4);
  qcopy(pts, buf, 48);
  vu_xform(pts, pts, view, 48);
  if (age > 5) age = 5;
  vu_sub(d, pts, pts + age * 16);
  vu_mul(sq, d, d);
  if (!near(sq)) return;
  set_view(view);
  gs_mode1(1);
  gs_mode2(2);
  ribbon(pts, age);
  ribbon(pts + 96, age);
}

/* ------------------------------------------------------------------------------------------------
 * Effect 10: Gokuu's own sword trail (JP 0x202b08 / PAL 0x202bb0).
 *
 * PAL keeps JP's spline ribbon and adds, for the player character (entity type 0), the look of its
 * pressure-sensitive attack strength (atk_level[0], PAL gp byte 0x51c61c): level 4 brightens the
 * ribbon, level 5 brightens it more, fills the blade edge and throws _light_k sparks off the blade
 * (160 particles, PAL's loader 0x202b10 sets them up).  The spline helper is JP's own 0x203380
 * (same interface; PAL recompiled it).
 * ------------------------------------------------------------------------------------------------ */
typedef struct { float x, y, z, w; } v4;

volatile u8 atk_level[3];              /* PAL gp-17748..-17746: strength of the current attack (3/4/5) */

#define ent_type(e)  (*(short *)((u8 *)(e) + 388))
#define TICK         (*(volatile u8 *)0x4f1460)      /* PAL gp-11984: logic frame flag */
#define TEX_GEFFECT  (*(int *)0x4f0e88)              /* JP loader 0x203890 ("Geffect/data") */
#define CAM_ANGLES   ((void *)0x61e7b0)              /* = PAL 0x63e4d0 */

#define jp_load10    ((void (*)(void))0x203890)
#define tex_find     ((int (*)(const char *))0x2f81f8)
#define view_a       ((int (*)(void))0x2f4360)
#define view_b       ((int (*)(void))0x2f4370)
#define mtx_ident    ((void (*)(void *))0x3c2a30)
#define mtx_scale    ((void (*)(void *, void *))0x2f4308)
#define mtx_trans    ((void (*)(void *, void *, void *))0x3c2988)
#define mtx_proj     ((void (*)(void *, void *, int, int))0x2f41f0)
#define set_tex      ((void (*)(int))0x2f7f78)
#define strip_clip   ((int (*)(u64 *, void *, void *, void *, void *, void *))0x2f9b44)
#define strip_draw   ((void (*)(u64 *))0x2f7668)
#define rand_        ((int (*)(void))0x3d3488)
#define sin_         ((float (*)(int))0x392170)
#define bill_rot     ((void (*)(void *, const void *, void *, int))0x2f4750)
#define sprite       ((void (*)(u64 *, void *, void *, int))0x2f5ac4)
#define vadd         ((void (*)(void *, void *, void *))0x2f9d64)
#define SPLINE       0x203380   /* (pts, out, n, work, f12 tension) */
#define VSCALE_N     0x2f9e1c   /* (out, in, n, f12 s) */
#define VSCALE       0x2f9e00   /* (out, in, f12 s) */

/* call a game routine that takes ints in a0-a3 plus a float in $f12 (n32 would put it in $f15) */
float f12call(u32 fn, u32 a0, u32 a1, u32 a2, u32 a3, float f);
__asm__(".set push\n.set noreorder\n.set hardfloat\n.globl f12call\nf12call:\n"
        "mov.s $f12,$f17\nmove $25,$4\nmove $4,$5\nmove $5,$6\nmove $6,$7\njr $25\nmove $7,$8\n.set pop\n");

#define NSPARK 160
static v4 spark_p[NSPARK] A16, spark_v[NSPARK] A16;
static short spark_life[NSPARK];
static short spark_i;
static int tex_light;

static const v4 one_w A16 = { 0, 0, 0, 1 };                                   /* PAL sp+560 */
static const v4 corner[2] A16 = { { -1, 1, 0, 1 }, { 1, -1, 0, 1 } };         /* PAL 0x3ed390 */
static const v4 origin A16 = { 0, 0, 0, 1 };                                  /* PAL 0x3ed380 */

static float bm[16] A16, wp[4] A16, m96[16] A16, m160[16] A16;
static v4 scl A16, zero4 A16, sq4[4] A16, uv[4] A16, rot2[2] A16, siz2[2] A16;
static u64 col[4] A16, spr[3] A16;

void my_load10(void)
{
  int i;
  jp_load10();
  tex_light = tex_find("Geffect/data/_light_k.rh2");
  for (i = 0; i < NSPARK; i++) spark_life[i] = 0;
  spark_i = 0;
}

static void copy16(u8 *d, const u8 *s) { ((u64 *)d)[0] = ((const u64 *)s)[0]; ((u64 *)d)[1] = ((const u64 *)s)[1]; }

static void edge_pos(void *ent, int bone, u8 *dst)
{
  bone_mtx(ent, bone, bm);
  mtx_view(wp, bm, (void *)&one_w);
  copy16(dst, (const u8 *)wp);
}

static void lerp(v4 *o, const v4 *a, const v4 *b, float t, float T)
{
  o->x = a->x + (b->x - a->x) * t / T;
  o->y = a->y + (b->y - a->y) * t / T;
  o->z = a->z + (b->z - a->z) * t / T;
  o->w = a->w;
}

void my_eff10(int slot, int *p)
{
  u8 *o = (u8 *)(EFF_OBJ + slot * 0x90);
  u8 *buf, *ent;
  int n, i, k, va, vb, cntA, cntB, lv, type0;
  short sh;
  u8 alpha;

  if (*(short *)(o + 8) == 0) {
    buf = alloc_(5072);
    *(void **)(o + 4) = buf;
    if (!buf) { *(short *)(o + 8) = -1; return; }
    *(short *)(buf + 5056) = 0;
    *(short *)(buf + 5058) = *(short *)((u8 *)p + 12);
    *(short *)(buf + 5060) = 0;
    buf[5062] = ((u8 *)p)[16]; buf[5063] = ((u8 *)p)[17]; buf[5064] = ((u8 *)p)[18];
    edge_pos((void *)p[0], p[1], buf);
    edge_pos((void *)p[0], p[2], buf + 256);
    for (k = 0; k < 15; k++) { copy16(buf + 16 + 16 * k, buf); copy16(buf + 256 + 16 + 16 * k, buf + 256); }
    return;
  }
  buf = *(u8 **)(o + 4);
  ent = (u8 *)p[0];
  va = view_a(); vb = view_b();
  if (!p[1] || !p[2]) goto tail;
  n = *(short *)((u8 *)p + 12);
  *(short *)(buf + 5058) = n;
  if (n == 0) goto tail;

  if (TICK) {
    u32 *fl = (u32 *)(ent + 192);
    if (*fl & 0x100000) { *fl &= ~0x180000u; *(short *)(buf + 5056) = 0; *(short *)(buf + 5060) = 0; }
    if (*fl & 0x80000) { sh = *(short *)(buf + 5060) + 1; *(short *)(buf + 5060) = sh > n ? n : sh; }
    else { sh = *(short *)(buf + 5060) - 1; *(short *)(buf + 5060) = sh < 0 ? 0 : sh; }
    sh = *(short *)(buf + 5056) + 1; *(short *)(buf + 5056) = sh > n ? n : sh;
    if (*(short *)(buf + 5060) > n) *(short *)(buf + 5060) = n;
  }
  sh = *(short *)(buf + 5060);
  if (sh == 0) *(short *)(buf + 5056) = 0;
  alpha = (u8)((sh << 7) / n);
  buf[5062] = ((u8 *)p)[16]; buf[5063] = ((u8 *)p)[17]; buf[5064] = ((u8 *)p)[18];
  type0 = ent_type(ent) == 0;
  lv = atk_level[0];
  if (type0) {
    if (lv == 5) alpha = (u8)((alpha + 256) / 3);
    else if (lv == 4) alpha = (u8)((alpha * 2 + 128) / 3);
  }
  if (TICK) {
    for (k = n - 1; k > 0; k--) { copy16(buf + 16 * k, buf + 16 * (k - 1)); copy16(buf + 256 + 16 * k, buf + 256 + 16 * (k - 1)); }
    edge_pos(ent, p[1], buf);
    edge_pos(ent, p[2], buf + 256);
  }
  n = *(short *)(buf + 5058);
  cntA = n * 8 - 7;
  cntB = *(short *)(buf + 5056) * 8 - 7;
  f12call(SPLINE, (u32)buf, (u32)(buf + 512), n, (u32)(buf + 4416), 1.0f);
  f12call(SPLINE, (u32)(buf + 256), (u32)(buf + 2464), n, (u32)(buf + 4416), 4.0f);
  copy16(buf + 512, buf);
  copy16(buf + 2464, buf + 256);
  copy16(buf + 512 + 16 * cntA, buf + 16 * (n - 1));
  copy16(buf + 2464 + 16 * cntA, buf + 256 + 16 * (n - 1));
  gs_mode1(1);
  if (*(short *)(buf + 5056) == 0) goto tail;

  scl.x = scl.y = scl.z = 1.0f; scl.w = 0;
  zero4.x = zero4.y = zero4.z = zero4.w = 0;
  mtx_ident(m96);
  mtx_scale(m96, &scl);
  mtx_trans(m96, m96, &zero4);
  mtx_proj(m160, m96, va, vb);
  vu_load(m160);
  for (i = 0; i < cntB; i++) {
    v4 *A = (v4 *)(buf + 512), *B = (v4 *)(buf + 2464);
    int den = cntB + i / 2;
    u8 c384 = (u8)(alpha * (cntB - i) / den), c385 = (u8)(alpha * (cntB - 1 - i) / den), c387 = 0;
    u64 rgb = buf[5062] | (u64)buf[5063] << 8 | (u64)buf[5064] << 16;
    float t = (float)i, T = (float)cntB, u = (float)(i + 1);
    if (type0) {
      if (lv == 5) { c384 = (u8)((c384 + 256) / 3); c385 = (u8)((c385 + 256) / 3); c387 = c385; }
      else if (lv == 4) { c385 = (u8)((c385 + 128) >> 1); c384 = (u8)((c384 + 128) >> 1); c387 = c385 >> 1; }
    }
    col[0] = rgb | (u64)c387 << 24; col[1] = rgb | (u64)c384 << 24;
    col[2] = rgb | (u64)c387 << 24; col[3] = rgb | (u64)c385 << 24;
    gs_mode2(2);
    lerp(&sq4[0], &A[i], &B[i], t, T);
    sq4[1] = B[i];
    lerp(&sq4[2], &A[i + 1], &B[i + 1], u, T);
    sq4[3] = B[i + 1];
    uv[0].x = 0.25f; uv[0].y = t / T; uv[0].z = uv[0].w = 0;
    uv[1].x = 0.75f; uv[1].y = t / T; uv[1].z = uv[1].w = 0;
    uv[2].x = 0.25f; uv[2].y = u / T; uv[2].z = uv[2].w = 0;
    uv[3].x = 0.75f; uv[3].y = u / T; uv[3].z = uv[3].w = 0;
    set_tex(TEX_GEFFECT);
    if (!strip_clip(col, &sq4[0], &sq4[1], &sq4[2], &sq4[3], uv)) strip_draw(col);

    if (type0 && lv == 5 && TICK) {     /* sparks off the blade */
      int h = cntB / 2, d = h - i, r;
      float w, s;
      v4 *P = &spark_p[spark_i], *V = &spark_v[spark_i];
      if (d < 0) d = -d;
      w = (float)(h - d) / (float)cntB * 4.0f;
      if (w <= 0.1f) w = 0.1f;
      if ((float)(rand_() % 20) <= w * 12.0f) {
        s = (float)(rand_() & 0x7fff) / 32767.0f;
        P->x = (sq4[0].x + sq4[2].x) * 0.5f + (float)((rand_() & 0x64) - 50) * 0.02f;
        P->y = (sq4[0].y + sq4[2].y) * 0.5f + (float)((rand_() & 0x64) - 50) * 0.02f;
        P->z = (sq4[0].z + sq4[2].z) * 0.5f + (float)((rand_() & 0x64) - 50) * 0.02f;
        P->w = 1.0f;
        s += 0.1f;
        V->x = (sq4[1].x - P->x) * s;
        V->y = (sq4[1].y - P->y) * s;
        V->z = (sq4[1].z - P->z) * s;
        r = (rand_() >> 27) % 20;
        if (r < 0) r = -r;
        spark_life[spark_i] = 20 - r;
        if (++spark_i == NSPARK) spark_i = 0;
      }
    }
  }
tail:
  if (ent_type(ent) != 0) return;
  if (TICK) for (i = 0; i < NSPARK; i++) if (spark_life[i] > 0) spark_life[i]--;
  gs_mode2(2);
  set_tex(tex_light);
  bill_rot(rot2, corner, CAM_ANGLES, 2);
  set_view((void *)&origin);
  {
    u32 base = (buf[5062] >> 1) | (buf[5063] >> 1) << 8 | ((buf[5064] + 255) >> 1) << 16;
    spr[1] = 0; spr[2] = 0x08000800;
    for (i = 0; i < NSPARK; i++) {
      float a, sz;
      if (spark_life[i] <= 0) continue;
      a = sin_(spark_life[i] * 819) * 255.0f;
      sz = sin_(spark_life[i] * 819);
      spr[0] = (u32)(base | (u32)(int)a << 24);
      f12call(VSCALE_N, (u32)siz2, (u32)rot2, 2, 0, sz);
      sprite(spr, &spark_p[i], siz2, 1);
      if (TICK) {
        vadd(&spark_p[i], &spark_p[i], &spark_v[i]);
        f12call(VSCALE, (u32)&spark_v[i], (u32)&spark_v[i], 0, 0, 0.5f);
      }
    }
  }
}
