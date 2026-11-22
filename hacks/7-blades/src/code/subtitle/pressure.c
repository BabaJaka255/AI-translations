/* PAL's pressure-sensitive attacks on the Japanese program (the project lead chose the full port, 2026-11-10).
 *
 * PAL samples the analogue button pressures for a few frames after Gokuu starts an attack and turns
 * the hardest press into an attack level kept in a gp byte (atk_level[0], PAL gp-17748):
 *   1 = sampling, 2 = read, 3 = light press (max < 55): half damage, 4 = normal, 5 = hard press
 *   (max >= 210): 1.5x damage, longer reach, wider swing arc, faster thrown blade, and effect 10
 *   draws the bright trail with sparks (fx.c).
 * Every routine here is the C form of the PAL code named next to it; the asm stubs at the bottom are
 * what b7_build_jp.py jumps to from the matching places in the JP code.  Yuri has her own copy
 * (lvl_y[0..1], PAL gp-17128/-17127): her shot speed, swing, shot damage and her hit routine.
 */
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;

#define GP          0x4f4df0                     /* PAL 0x520b70 */
#define PLAYER      (*(u32 *)(GP - 16412))       /* PAL gp-13836 */
#define DEMO        (*(volatile u8 *)(GP - 16496))   /* PAL gp-13920 (0x51d510) */
#define PAD_STATUS  ((volatile int *)(GP - 15008))   /* PAL gp-12288 */
#define PAD_DATA    0x5327f4                     /* PAL 0x552074, 384 bytes per port; pressures at +8 */
#define BTN_CFG     ((volatile int *)0x478830)   /* PAL 0x49c4c0: button mask per config slot */

#define jp_padget   ((int (*)(int, int, u8 *))0x384568)   /* PAL 0x38a8c8 without the sampling */
#define pad_full    ((int (*)(int, int))0x3bf318)         /* PAL 0x3c1c08: 1 if the pad reports all 18 buttons */

extern volatile u8 atk_level[3];                 /* fx.c; PAL gp-17748..-17746 */

/* ---- sampling, PAL 0x38a8c8 / 0x38b308 / 0x38abc8 ---- */
static short pw_win[2];                          /* PAL gp-12280 */
static short pw_cnt[2][12], pw_max[2][12], pw_sum[2][12], pw_min[2][12];   /* PAL 0x552240/70/a0/d0 */

static void pw_clear(int pad)
{
  int i;
  for (i = 0; i < 12; i++) pw_cnt[pad][i] = pw_max[pad][i] = pw_sum[pad][i] = pw_min[pad][i] = 0;
}

/* replaces the JP pad read at its two callers (0x3b4e40, 0x3baa6c) */
int my_padget(int pad, int unused, u8 *out)
{
  int r = jp_padget(pad, unused, out), i;
  if ((u32)pad < 2 && PAD_STATUS[pad] == 1 && pw_win[pad] > 0) {
    const volatile u8 *p = (const volatile u8 *)(PAD_DATA + pad * 384 + 8);
    pw_win[pad]--;
    for (i = 0; i < 12; i++) {
      short a = p[i];
      if (!a || pw_cnt[pad][i] >= 10) continue;
      pw_cnt[pad][i]++;
      if (pw_max[pad][i] < a) pw_max[pad][i] = a;
      if (a < pw_min[pad][i] || pw_min[pad][i] == 0) pw_min[pad][i] = a;
      pw_sum[pad][i] += a;
    }
  }
  return r;
}

static int pw_start(int pad, int frames)        /* PAL 0x38b308 */
{
  if ((u32)pad >= 2 || pad_full(pad, 0) != 1) return 0;
  pw_win[pad] = frames;
  pw_clear(pad);
  return 1;
}

static int pw_read(int pad, int b, short *out)  /* PAL 0x38abc8 */
{
  if ((u32)pad >= 2 || (u32)b >= 12 || !out || pad_full(pad, 0) != 1 || !pw_cnt[pad][b]) return 0;
  out[0] = pw_max[pad][b]; out[1] = pw_min[pad][b]; out[3] = pw_sum[pad][b]; out[4] = pw_cnt[pad][b];
  out[2] = out[3] / out[4];
  pw_cnt[pad][b] = pw_max[pad][b] = pw_sum[pad][b] = pw_min[pad][b] = 0;
  return 1;
}

static int pw_read_btn(int pad, int id, short *out)   /* PAL 0x3bcad8: game button id -> pressure byte */
{
  static const u8 mask[8] = { 0x10, 0x20, 0x40, 0x80, 4, 8, 1, 2 };            /* ids 4..11 */
  static const signed char idx[10] = { 5, 4, 6, 7, 8, 9, -1, -1, 11, 10 };     /* config slot -> byte */
  int m = -1, s, b = id;
  if (DEMO) return 0;
  if ((u32)(id - 4) < 8) m = mask[id - 4];
  for (s = 0; s < 10 && BTN_CFG[s] != m; s++) ;
  if (s < 10 && idx[s] >= 0) b = idx[s];
  return pw_read(pad, b, out);
}

/* ---- PAL 0x25c380: turn the samples into the attack level, scale a damage record ---- */
static short tbl5[5], tbl4[5];                   /* PAL 0x40ee40 (circle), 0x40ee50 (triangle) */

static void level_fn(u32 ent, int id, volatile u8 *lvl, short *tbl, u8 *rec)
{
  int l = *lvl, t;
  if (ent != PLAYER) { *lvl = 0; return; }
  if (l == 4) return;
  if (DEMO) { *lvl = 4; return; }
  if (l == 1) {
    if (pw_read_btn(0, id, tbl) != 1) { *lvl = 4; return; }
    l = 2; *lvl = 2;
  }
  if (l < 2) return;
  if (tbl[0] >= 210) {
    if (rec) {
      *(u32 *)(rec + 8) = (u32)(int)((float)(int)*(u32 *)(rec + 8) * 1.5f);
      t = rec[6] & 15;
      if (t == 2 || t == 5) rec[6] = 4;
      else if (t < 2) rec[6]++;
    }
    *lvl = 5;
  } else if (tbl[0] >= 55) {
    *lvl = 4;
  } else {
    if (rec) {
      *(u32 *)(rec + 8) = (u32)(int)((float)(int)*(u32 *)(rec + 8) * 0.5f);
      t = rec[6] & 15;
      if (t == 1 || t == 2) rec[6]--;
      else if (t == 3 || t == 4) rec[6] = 2;
      else if (t == 5) rec[6] = 1;
      else if (t == 6) rec[6] = 0;
    }
    *lvl = 3;
  }
}

/* ---- hooks (called from the stubs below) ---- */
volatile int act_orig;                              /* action passed to 0x258d58 (PAL 0x254de0) */
float rng_near = 50.0f, rng_far = 100.0f;        /* PAL gp-13208 / gp-13212 */
float f_speed = 4.0f;

/* end of the action function: PAL's s5 (start sampling) and s7 (clear the level) flags */
void hk_act_tail(u32 ent, int motion, int fin)
{
  int a = act_orig, s5 = 0, s7 = 1;
  switch (a) {
  case 178: case 352: case 287: case 320: case 420: case 170: case 171: case 380: case 386:
  case 193: case 194: case 201: case 202: case 203: case 211: case 219: case 220: case 229: case 230:
  case 237: case 245: case 264: case 265: case 272: case 280: case 298: case 299: case 302: case 303:
  case 330: case 331: case 334: case 335: case 336: case 345: case 363: case 364: case 367: case 368:
  case 369: case 370: case 371: case 372: case 396: case 398: case 399: case 406: case 417: case 459:
  case 252: case 392: case 346: case 408:
    s5 = 1; break;
  case 311:
    if ((u32)(motion - 314) < 3 || motion == 319) s7 = 0; else s5 = 1;
    break;
  case 395: case 294: case 328: case 360: case 437: case 223: case 224: case 394:
  case 312: case 313: case 325:
    s7 = 0; break;
  case 19: case 20:                              /* weapon attacks: PAL starts sampling once remapped */
    if (fin != a) s5 = 1;
    break;
  }
  if (s7) atk_level[0] = 0;
  if (s5 && ent == PLAYER && pw_start(0, 5) == 1) atk_level[0] = 1;
}

void hk_hitbox(u32 ent)                          /* PAL 0x278070 +0x1a4 */
{
  level_fn(ent, 5, &atk_level[0], tbl5, 0);
  atk_level[1] = atk_level[0];
  if (atk_level[0] == 5) { rng_far = 150.0f; rng_near = 75.0f; }
  else { rng_far = 100.0f; rng_near = 50.0f; }
}

void hk_rec(u8 *rec, int site)                   /* PAL 0x2798e0: the two hit records */
{
  int l = atk_level[1];
  if (l == 5) { rec[6] = site ? 2 : 4; *(u32 *)(rec + 8) = site ? 48 : 96; }
  else if (l == 3) { rec[6] = site ? 0 : 1; *(u32 *)(rec + 8) = site ? 24 : 48; }
}

void hk_hit(u32 ent, int act, u8 *rec)           /* PAL 0x25c578 +0x584 */
{
  if (act < 179) level_fn(ent, 4, &atk_level[0], tbl4, rec);
  else level_fn(ent, 5, &atk_level[0], tbl5, rec);
}

void hk_throw(u32 ent)                           /* PAL 0x2ba550 +0x48 */
{
  level_fn(ent, 5, &atk_level[0], tbl5, 0);
  atk_level[2] = atk_level[0];
  f_speed = atk_level[2] == 5 ? 6.0f : 4.0f;
}

/* ---- Yuri (PAL gp-17128 / -17127) ---- */
volatile u8 lvl_y[2];
static short tbly[5];                            /* PAL 0x437da0 */
float y_speed = 1.5f;

void hk_ystart(u32 ent)                          /* PAL 0x2c2850 +0x440: her attack starts sampling */
{
  if (ent == PLAYER && pw_start(0, 5) == 1) lvl_y[0] = 1;
}

void hk_yshot(u32 ent)                           /* PAL 0x2c89a0 +0x44c: shot speed 1.5, 3 at level 5 */
{
  level_fn(ent, 5, &lvl_y[0], tbly, 0);
  lvl_y[1] = lvl_y[0];
  y_speed = lvl_y[1] == 5 ? 3.0f : 1.5f;
}

/* PAL 0x2c9c80: Yuri's hit routine (entity +108), JP's generic 0x3a6188 with PAL's changes:
   pressure level on the hit record, motion 243 damage 15 / 5 / 1 */
#define mot_id     ((int (*)(u32))0x383930)
#define mot_frame  ((int (*)(u32))0x383938)
#define mot_len    ((int (*)(u32))0x383960)
#define hit_test   ((int (*)(u32, u8 *, int, int))0x3a8278)
#define hit_next   ((int (*)(u32, u8 *, u8 *, int, int))0x3a86b0)
#define hit_apply  ((int (*)(u8 *, u8 *, u8 *))0x3a5828)
#define hit_react  ((void (*)(u8 *))0x3a60b8)
#define jp_memset  ((void (*)(void *, int, int))0x3d3318)
#define HIT_FLAG   (*(volatile int *)(GP - 16592))
#define HIT_BUF    ((void *)0x48cc18)

int my_yuri_hit(u8 *ent)
{
  static u8 buf[48] __attribute__((aligned(16)));   /* PAL sp+0 (16), record sp+16, state sp+32 */
  u32 mdl = *(u32 *)ent;
  int mot = mot_id(mdl), fr = mot_frame(mdl), n = mot_len(mdl), hits = 0;
  u8 *rec = buf + 16;
  if (fr == n) fr--;
  if (n > 0 && n < fr) fr %= n;
  if (!hit_test(*(u32 *)(ent + 144), rec, mot, fr)) return 0;
  level_fn((u32)ent, 5, &lvl_y[0], tbly, rec);
  if (mot == 243) {
    rec[3] |= 0x20;
    *(u32 *)(rec + 8) = lvl_y[0] == 5 ? 15 : lvl_y[0] == 3 ? 1 : 5;
  }
  if ((rec[3] & 2) && mot != 100 && (*(u32 *)(*(u32 *)mdl + 32) & 0x20)) hit_react(ent);
  HIT_FLAG = 0;
  jp_memset(HIT_BUF, 0, 1280);
  *(int *)(buf + 32) = 0;
  while (hit_next(*(u32 *)(ent + 144), buf, buf + 32, mot, fr)) {
    int r = hit_apply(ent, buf, rec);
    HIT_FLAG = 1;
    if (r) hits++;
  }
  HIT_FLAG = 0;
  jp_memset(HIT_BUF, 0, 1280);
  return hits;
}

/* ---- asm stubs ----
 * CALL saves every caller-saved register (and hi/lo, $f0-$f19), calls a C hook with a0..a2 taken
 * from the given registers, and restores them, so it can sit anywhere in the game's code. */
__asm__(
".set push\n.set noreorder\n.set noat\n.set hardfloat\n"
".macro SAVE\n"
" addiu $sp,$sp,-240\n"
" sd $2,0($sp); sd $3,8($sp); sd $4,16($sp); sd $5,24($sp); sd $6,32($sp); sd $7,40($sp)\n"
" sd $8,48($sp); sd $9,56($sp); sd $10,64($sp); sd $11,72($sp); sd $12,80($sp); sd $13,88($sp)\n"
" sd $14,96($sp); sd $15,104($sp); sd $24,112($sp); sd $25,120($sp); sd $31,128($sp)\n"
" mfhi $8; sd $8,136($sp); mflo $8; sd $8,144($sp)\n"
" swc1 $f0,152($sp); swc1 $f1,156($sp); swc1 $f2,160($sp); swc1 $f3,164($sp); swc1 $f4,168($sp)\n"
" swc1 $f5,172($sp); swc1 $f6,176($sp); swc1 $f7,180($sp); swc1 $f8,184($sp); swc1 $f9,188($sp)\n"
" swc1 $f10,192($sp); swc1 $f11,196($sp); swc1 $f12,200($sp); swc1 $f13,204($sp); swc1 $f14,208($sp)\n"
" swc1 $f15,212($sp); swc1 $f16,216($sp); swc1 $f17,220($sp); swc1 $f18,224($sp); swc1 $f19,228($sp)\n"
".endm\n"
".macro RESTORE\n"
" lwc1 $f0,152($sp); lwc1 $f1,156($sp); lwc1 $f2,160($sp); lwc1 $f3,164($sp); lwc1 $f4,168($sp)\n"
" lwc1 $f5,172($sp); lwc1 $f6,176($sp); lwc1 $f7,180($sp); lwc1 $f8,184($sp); lwc1 $f9,188($sp)\n"
" lwc1 $f10,192($sp); lwc1 $f11,196($sp); lwc1 $f12,200($sp); lwc1 $f13,204($sp); lwc1 $f14,208($sp)\n"
" lwc1 $f15,212($sp); lwc1 $f16,216($sp); lwc1 $f17,220($sp); lwc1 $f18,224($sp); lwc1 $f19,228($sp)\n"
" ld $8,136($sp); mthi $8; ld $8,144($sp); mtlo $8\n"
" ld $2,0($sp); ld $3,8($sp); ld $4,16($sp); ld $5,24($sp); ld $6,32($sp); ld $7,40($sp)\n"
" ld $8,48($sp); ld $9,56($sp); ld $10,64($sp); ld $11,72($sp); ld $12,80($sp); ld $13,88($sp)\n"
" ld $14,96($sp); ld $15,104($sp); ld $24,112($sp); ld $25,120($sp); ld $31,128($sp)\n"
" addiu $sp,$sp,240\n"
".endm\n"

/* 0x258d88 jal 0x383950: remember the action the function was called with (s3 = a1) */
".globl st_act_in\nst_act_in:\n"
" lui $1,%hi(act_orig)\n sw $19,%lo(act_orig)($1)\n j 0x383950\n nop\n"

/* 0x259f04 jal 0x383870 (a0 model, a1 final action, a2): s1 entity, s4 motion, s3 final action */
".globl st_act_out\nst_act_out:\n"
" SAVE\n move $4,$17\n move $5,$20\n jal hk_act_tail\n move $6,$19\n RESTORE\n j 0x383870\n nop\n"

/* 0x27df5c jal 0x3920b8 inside the hitbox setup 0x27de00 (PAL 0x278070): s2 = attacker */
".globl st_hitbox\nst_hitbox:\n"
" SAVE\n jal hk_hitbox\n move $4,$18\n RESTORE\n j 0x3920b8\n nop\n"

/* 0x27e950..0x27e9b8 in the swing test 0x27e688 (PAL 0x278968 +0x294): sector of the swing angle s7,
   12288 wide instead of 8192 at level 5, and the last sector's offset from 0x9000 instead of 0x6000 */
".globl st_arc\nst_arc:\n"
" lui $1,%hi(atk_level+1)\n lbu $4,%lo(atk_level+1)($1)\n li $2,5\n bne $4,$2,1f\n li $2,12288\n"
" div $0,$23,$2\n mflo $22\n b 2f\n nop\n"
"1: li $4,-1\n addiu $2,$23,8191\n slt $3,$4,$23\n movn $2,$23,$3\n sra $22,$2,13\n"
"2: slti $2,$22,4\n li $6,3\n movz $22,$6,$2\n lw $5,-15832($28)\n li $7,1\n"
" bne $5,$7,3f\n nop\n sll $3,$21,2\n xori $2,$22,1\n movz $21,$3,$2\n"
"3: bne $22,$6,5f\n nop\n sll $21,$21,2\n"
" lui $1,%hi(atk_level+1)\n lbu $4,%lo(atk_level+1)($1)\n li $2,5\n bne $4,$2,4f\n nop\n"
" li $2,-36864\n addu $2,$23,$2\n addiu $3,$2,1023\n li $4,-1\n slt $4,$4,$2\n movn $3,$2,$4\n"
" sra $3,$3,10\n b 5f\n addu $21,$21,$3\n"
"4: addiu $2,$23,-24576\n addiu $3,$23,-23553\n li $4,-1\n slt $4,$4,$2\n movn $3,$2,$4\n"
" sra $3,$3,10\n addu $21,$21,$3\n"
"5: li $2,2\n bne $22,$2,6f\n nop\n sll $2,$21,2\n addu $21,$2,$21\n"
"6: li $4,-1\n j 0x27e9bc\n nop\n"

/* 0x27f018: angle limit for the swing hitting from behind, 16384 -> 24576 at level 5 */
".globl st_arc2\nst_arc2:\n"
" move $3,$2\n lui $1,%hi(atk_level+1)\n lbu $4,%lo(atk_level+1)($1)\n li $2,5\n bne $4,$2,1f\n"
" slti $2,$23,16384\n slti $2,$23,24576\n"
"1: bnez $3,2f\n nop\n j 0x27f03c\n nop\n"
"2: j 0x27f024\n nop\n"

/* 0x27f198: knock-back angle floor for the struck enemy, 0x6000 -> 0x9000 at level 5 */
".globl st_arc3\nst_arc3:\n"
" lui $1,%hi(atk_level+1)\n lbu $4,%lo(atk_level+1)($1)\n li $2,5\n bne $4,$2,1f\n lw $3,256($19)\n"
" li $2,0x8fff\n slt $2,$2,$3\n bnez $2,2f\n li $2,0x9000\n b 2f\n sw $2,256($19)\n"
"1: slti $2,$3,24576\n beqz $2,2f\n li $2,24576\n sw $2,256($19)\n"
"2: j 0x27f1ac\n nop\n"

/* 0x27f744 / 0x27f7a0 jal 0x3a5828 with the hit record at a2 (PAL 0x2798e0) */
".globl st_recA\nst_recA:\n"
" SAVE\n move $4,$6\n jal hk_rec\n li $5,0\n RESTORE\n j 0x3a5828\n nop\n"
".globl st_recB\nst_recB:\n"
" SAVE\n move $4,$6\n jal hk_rec\n li $5,1\n RESTORE\n j 0x3a5828\n nop\n"

/* 0x260608 in the hit handler 0x260170: s1 attacker, s0 action, s6 = hit record; then bne s0,470 */
".globl st_hit\nst_hit:\n"
" SAVE\n move $4,$17\n move $5,$16\n jal hk_hit\n move $6,$22\n RESTORE\n"
" li $1,470\n bne $16,$1,1f\n nop\n j 0x260610\n nop\n1: j 0x260644\n nop\n"

/* 0x265cc4 beqz v0,0x265e34: PAL also runs 0x2623c8 when the attack was a light press (level 3) */
".globl st_light\nst_light:\n"
" bnez $2,1f\n nop\n lui $1,%hi(atk_level)\n lbu $3,%lo(atk_level)($1)\n li $2,3\n beq $3,$2,1f\n nop\n"
" j 0x265e34\n nop\n1: j 0x265ccc\n nop\n"

/* 0x2694a4 (player branch of 0x269448): PAL also clears the attack level */
".globl st_clr\nst_clr:\n"
" lui $1,%hi(atk_level)\n sb $0,%lo(atk_level)($1)\n lw $2,204($7)\n j 0x2694ac\n nop\n"

/* 0x2c2d78 (thrown blade 0x2c2cf8, PAL 0x2ba550): speed 4, or 6 at level 5; called with jal */
".globl st_throw\nst_throw:\n"
" SAVE\n jal hk_throw\n move $4,$18\n RESTORE\n lui $1,%hi(f_speed)\n jr $31\n lwc1 $f0,%lo(f_speed)($1)\n"
/* Yuri's action function 0x2cb078 (PAL 0x2c2850): clears her level on entry */
".globl st_yact\nst_yact:\n"
" addiu $sp,$sp,-96\n sd $20,64($sp)\n lui $1,%hi(lvl_y)\n sb $0,%lo(lvl_y)($1)\n"
" j 0x2cb080\n nop\n"

/* 0x2cb4b4 b 0x2cbb24 (case at PAL 0x2c2c90): s1 = entity */
".globl st_ystart\nst_ystart:\n"
" SAVE\n jal hk_ystart\n move $4,$17\n RESTORE\n j 0x2cbb24\n nop\n"

/* 0x2d14bc in 0x2d1070 (PAL 0x2c89a0): s4 = Yuri, f0 = shot speed, then lw a3,548(sp) ... */
".globl st_yshot\nst_yshot:\n"
" SAVE\n jal hk_yshot\n move $4,$20\n RESTORE\n lui $1,%hi(y_speed)\n lwc1 $f0,%lo(y_speed)($1)\n j 0x2d14c4\n nop\n"

/* 0x2d1c98 (PAL 0x2c9608): swing turn -6144, -3072 at level 5 */
".globl st_yswing\nst_yswing:\n"
" lui $1,%hi(lvl_y)\n lbu $3,%lo(lvl_y)($1)\n lw $2,172($5)\n li $1,5\n bne $3,$1,1f\n addiu $2,$2,-6144\n"
" addiu $2,$2,3072\n1: j 0x2d1ca4\n nop\n"

/* 0x244cfc (shot hit records 0x244b80, PAL 0x240aa0 +0x16c): record 3 damage 3, 10 at level 5, 1 at level 3 */
".globl st_ydmg\nst_ydmg:\n"
" lui $1,%hi(lvl_y+1)\n lbu $3,%lo(lvl_y+1)($1)\n li $5,10\n li $1,5\n beq $3,$1,1f\n li $1,3\n"
" li $5,1\n beq $3,$1,1f\n nop\n li $5,3\n"
"1: sw $5,24($sp)\n lui $1,0x3fc0\n mtc1 $1,$f21\n sb $0,23($sp)\n j 0x244d3c\n nop\n"
".set pop\n");
