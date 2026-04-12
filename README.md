# PBO-Project-Mandiri
Are you a complete masochist who likes playing Soulslike or Bullet-hell?
But you feel like one of them isnt enough?

Introducing "Maidenless Danmaku"
Heavily inspired (kind of copied ngl) by Touhou: Hero of the ice fairy

A combination of BOTH
so you can suffer more hahajahahahja

Credits
Me - Coded
Lovely feet - helped create the design (friend)
Caitlynn - ideas and suggestion (friend)

JDWasabi - some sfx (guy on itch.io)
Chequered Ink - some sfx (guy on itch.io)

Inspiration : Touhou: Hero of the Ice Fairy.

HOW TO PLAY
W = Jump or up
A = Left
D = Right
S = Quick-fall or down

1 or 2 = Change attack type
K or M1 = Attack
L or M2 = Absorb
LSHIFT = Phase
Esc = Pause
R = Retry (when game over / finished)

Objective - Kill bosses, or smthng idk

Mechanic:
 - Action cd: an internal cd for each action like attacking, and parrying. can only do action when there is no cooldown, succesful action leads to lower cd
 - Attack:  >Slash : Short-ranged attack, short duration, short cd
            >Pierce : Long-ranged attack, mid duration, long cd
            >Spin? : not yet implemented
 - Phasing : will phase through bullets, last 2 sec max, will recharge, cannot do action while phasing 
 - Absorb: will absorb bullets in vicinity, successfully absorbing 1 bullet grant 1 stack of Baka(limit 3 stack per absorb window), 5 Baka stacks heals 1 HP

Customization: 
    Stages; 
    amount of Boss(es) per stage; 
    Boss pattern per phase (max_hp, move_speed, y_axis, bullet_rate, pattern: 'fan';'circle';'chaos';'random', 
                            num_bullet, bullet_spd, bullet_size, color, image: 'bullet-orb';'bullet-1';'bullet-2';'bullet-3')
    Player attack types (slash, pierce, spin)

you can -add 
    as many bosses as you want per stage (max it to 5 boss per arena, any more and ur cooked, and 3 is already chaotic too) 
    as many stages(WIP)
    as many platform as you want on a stage
    
in the same Game loop

im finna get copyrighted bruh
this game literally looks like a chopped version of Touhou: Hero of the ice fairy





========= Main Feature ============

Sistem Boss Multi-Fase — Setiap boss memiliki beberapa fase dengan pola gerakan dan serangan yang berbeda, semakin sulit di setiap fase
Sistem Stamina — Stamina digunakan untuk attack dan dapat habis, memaksa pemain untuk mengatur serangan secara strategis
Sistem Absorb — Pemain dapat menyerap peluru musuh untuk menambah stack Baka, 5 stack bisa heal player 1hp
Sistem Phase (Phasing) — Pemain dapat melewati peluru dengan menggunakan phase bar
Pola Peluru Beragam — Boss menggunakan 9 pola serangan: fan, circle, chaos, random, spiral, burst, cross, aimed, dan random
Stage Manager — Sistem manajemen stage yang mendukung multiple arena dengan boss, platform, dan background berbeda per stage (kurang assets for BG and Platform)
Kamera Dinamis — Kamera mengikuti pemain dengan smooth follow dan efek camera shake saat terkena serangan
Boss Acak — Stage dapat menggunakan boss yang digenerate secara prosedural dengan stat, pola, dan fase yang acak
UI Informatif — HUD menampilkan HP, stamina, phase bar, hotbar serangan, radial absorb timer, dan boss HP bar secara real-time

Unimplemented / Half-Executed feature
GUI - too lazy, atleast until more than 2 Stages
SFX - half-way there, too lazy to continue (finding sfx is hard)
BGM - even harder than sfx
Textures/Stages - too lazy, asked AI to generate some
Attacks - too lazy for keyframe editing
Animation - as you have guessed, too lazy
Game Balancing - i tried my best ;-; 


========= Technical Description ============

Proyek ini dirancang dengan menerapkan prinsip Pemrograman Berorientasi Objek (OOP) sebagai fondasi utamanya dan ini adalah beberapa penjelasan singkat
mengenai beberapa sistem game "Maidenless Danmaku":

Entity System
Semua entitas game (Player, Boss, Bullet) mewarisi dari GameObject, yang mengelola posisi, hitbox persegi, hitbox lingkaran, dan rendering sprite. Posisi disimpan sebagai float (posX, posY) untuk pergerakan yang halus, lalu disinkronkan ke pygame.Rect setiap frame melalui sync_rect() (khusus Boss dan Bullet).

Image Cache
Asset gambar dimuat sekali dan disimpan dalam dictionary image_cache dengan key berupa tuple (path, size, scale, flipx, flipy, angle). Ini mencegah pembacaan disk berulang dan memungkinkan preloading seluruh variasi rotasi peluru saat loading screen.

Collision Detection
Tabrakan antara peluru dan pemain menggunakan circle collision (circle_collide()) berdasarkan rumus jarak Euclidean, memberikan hitbox yang lebih akurat dan adil dibanding rectangle collision untuk objek yang bergerak cepat.

Boss & Stage Data (JSON-Driven)
Seluruh data boss dan stage disimpan dalam file JSON, memisahkan data dari logika game. Boss mendukung konfigurasi per-fase untuk HP, pola tembak, kecepatan, dan jenis gerakan. Stage mendefinisikan background, platform, dan daftar boss yang akan dimunculkan.

Kamera
Sistem kamera menghitung target offset berdasarkan posisi pemain dan margin layar, lalu melakukan interpolasi linear (lerp) setiap frame untuk efek smooth follow. Camera shake diimplementasikan dengan menambahkan offset acak selama durasi tertentu.


Sistem Serangan (Chain Hitbox)
Serangan pemain menggunakan sistem chain hitbox — serangkaian pygame.Rect kecil yang disusun memanjang dari posisi pemain ke arah cursor, membentuk jalur serangan. Hitbox-hitbox ini digenerate sekali saat serangan dipicu (_generate_attack_hitbox()), lalu sebagian darinya diaktifkan secara bertahap tiap frame berdasarkan animasi yang sedang berjalan (_attacking()).

    Alur kerja serangan:

Trigger — Pemain klik kiri atau tekan K. Arah serangan dihitung dari sudut antara posisi pemain dan cursor menggunakan math.atan2, lalu di-snap ke kelipatan 15°
Generate Hitbox — _generate_attack_hitbox() membuat n=8 rect yang tersusun di sepanjang vektor arah serangan, dengan panjang dan ketebalan berbeda tergantung jenis serangan
Active Frame Window — Setiap jenis serangan memiliki active_frames: [start, end] yang didefinisikan di JSON. Hitbox hanya aktif saat frame animasi berada di dalam window ini
Sweep per Jenis Serangan:

slash — Hitbox aktif bergerak seperti sapuan: hanya sebagian kecil (4 rect) di ujung depan yang aktif, bergeser dari pangkal ke ujung seiring progress animasi. Cocok untuk serangan area melengkung
pierce — Hitbox tumbuh dari pangkal ke ujung (grow): semakin banyak rect yang aktif seiring animasi berjalan. Cocok untuk tusukan yang menembus
default — Seluruh hitbox aktif sekaligus (spin / all-at-once) (not yet implemented, no animation for it)

Damage Tick — Serangan mendukung dua mode kerusakan: single (hanya sekali per musuh per serangan) dan multi (hit setiap 0.15 detik selama kontak)
Cleanup — Serangan dihapus dari active_attacks otomatis saat cur_frame melampaui frame_count



========= Struktur Project ============

project/
├── main.py                  # Entry point, game loop utama
├── Entities/
│   ├── Player.py            # Logika pemain, input, serangan, dan collision
│   ├── Boss.py              # Logika boss, gerakan, dan pola tembak
│   ├── Bullet.py            # Entitas peluru
│   ├── GameObject.py        # Base class untuk semua entitas
│   └── Particle.py          # Sistem partikel untuk efek visual
├── Systems/
│   ├── Camera.py            # Sistem kamera dengan smooth follow dan screen shake
│   ├── StageManager.py      # Manajemen stage, loading, dan entity update
│   └── ui.py                # Rendering seluruh elemen HUD
├── Shared/
│   ├── constants.py         # Konstanta global (resolusi, warna, flag debug)
│   └── utils.py             # Fungsi utilitas (image cache, sound cache, draw helpers)
├── assets/
│   ├── bgm/                 # File musik latar (.ogg / .mp3)
│   ├── sfx/                 # File efek suara (.wav)
│   ├── bullet/              # Sprite peluru
│   ├── cirno/               # Sprite karakter pemain
│   ├── ui/                  # Asset UI (hp bar, ikon, dll)
│   └── Cirno.ttf            # Font kustom
└── data/
    ├── stages/              # Data stage dalam format JSON
    ├── bosses/              # Data boss dalam format JSON
    └── player/              # Data pemain dan serangan dalam format JSON