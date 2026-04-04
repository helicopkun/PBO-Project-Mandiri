# PBO-Project-Mandiri
Are you a complete masochist who likes playing Soulslike or Bullet-hell?
But you feel like one of them isnt enough?

Introducing "Maidenless Danmaku"
Heavily inspired (kind of copied ngl) by Touhou: Hero of the ice fairy

A combination of BOTH
so you can suffer more hahajahahahja

HOW TO PLAY
W = Jump or up
A = Left
D = Right
S = Quick-fall or down

K or M1 = Attack
L or M2 = Absorb
LSHIFT = Phase

Objective - Kill bosses, or smthng idk

Mechanic:
 - Action cd: an internal cd for each action like attacking, and parrying. can only do action when there is no cooldown, succesful action leads to lower cd
 - Attack:  >Slash : Mid-ranged attack, short duration, short cd
            >Pierce : Long-ranged attack, mid duration, long cd
            >Spin? : not yet implemented
 - Phasing : will phase through bullets, last 2 sec max, will recharge, cannot do action while phasing 
 - Absorb: will absorb bullets in vicinity, successfully absorbing 1 bullet grant 1 stack of Baka, 5 Baka stacks heals 1 HP

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

Credits
Me - Coded
Lovely feet - helped create the design
Caitlynn - some nice idea and suggestion
Inspiration : Touhou: Hero of the Ice Fairy.





============================================ Technical Description =====================================================================================================

Proyek ini dirancang dengan menerapkan prinsip Pemrograman Berorientasi Objek (OOP) sebagai fondasi utamanya dan ini adalah beberapa penjelasan singkat
mengenai beberapa sistem game "Maidenless Danmaku":

1. Hierarki GameObject
    Setiap entitas dalam game (Pemain, Boss, Platform, dan Peluru) merupakan turunan dari base class GameObject. Struktur ini memungkinkan:
        Fisika Terenkapsulasi: 
        Penanganan hitbox berbasis Rect (persegi) maupun Circle (lingkaran) dikelola secara terpusat dalam satu kelas.

        Polimorfisme: 
        Setiap entitas mengimplementasikan logika update() dan draw() mereka sendiri, namun tetap menggunakan mesin rendering yang sama pada  world-surface.

2. Player Feature
    Sistem Pergerakan (move):
        Delta-Time (dt) Scaling: 
        Memastikan kecepatan gerak konsisten di berbagai frame rate (FPS).

        State Priority: 
        Mengatur urutan logika antara gravitasi, jumping state, dan clamping Platform untuk mencegah karakter bergetar (jitter) saat mendarat.

        Mekanisme Berbasis Waktu:
        Fitur Quick-fall dan Jump Recovery dikelola menggunakan stopwatch internal (elapsed timers). Pemain harus menekan tombol melampaui durasi threshold tertentu untuk memicu aksi, memberikan kontrol yang lebih taktil dan responsif.

        Logika Crossover (Sticky Zone): 
        Untuk mencegah efek Tunneling (karakter menembus Platform saat bergerak terlalu cepat), game ini menggunakan logika perbandingan posisi old_bottom (posisi frame sebelumnya) dengan posisi saat ini untuk memastikan pendaratan yang presisi pada platform.

    Sistem Serangan (attack)
        Rotasi & Penskalaan Dinamis:
        Posisi dan sudut seluruh rantai hitbox dihitung secara real-time berdasarkan arah hadap karakter atau posisi mouse. Hal ini memberikan fleksibilitas serangan yang dinamis di ruang dua dimensi tanpa memerlukan aset gambar yang banyak untuk setiap sudut arah.

        Sistem Hitbox Berantai (Chain Hitbox Style):
        Berbeda dengan hitbox persegi tunggal yang sering terdistorsi saat diputar, sistem ini menggunakan serangkaian lingkaran kolisi kecil yang disusun berantai. Hal ini memungkinkan gambar senjata/serangan diputar secara bebas (360 derajat tapi di snap 15*) sementara area deteksi serangan tetap presisi dan mengikuti bentuk visual tanpa perubahan skala (distortion-free).

        Logika Active Frames:
        Mengadopsi mekanik fighting game profesional, di mana serangan dibagi menjadi fase-fase spesifik. Hitbox hanya akan aktif dan mampu menghasilkan damage pada frame tertentu dalam sebuah animasi. Ini mencegah serangan terasa "setiap saat aktif" dan memaksa pemain untuk memperhatikan timing serangan mereka.

        Durasi Berbasis Animasi (Animation-Based Duration):
        Durasi hidup (lifetime) sebuah serangan tidak ditentukan oleh timer statis, melainkan terikat langsung pada progres frame animasi. Sinkronisasi ini memastikan bahwa apa yang dilihat pemain di layar (visual) selalu akurat dengan apa yang terjadi di mesin deteksi kolisi (mekanik).

        Dynamic Hitbox Slicing (Sweep & Grow Effect):
        Mekanisme hitbox menggunakan teknik List Slicing yang terikat pada progres frame animasi. Sistem menghitung "Leading Edge" (ujung depan) dan "Trailing Edge" (ekor belakang) secara real-time. Hal ini memastikan area serangan tidak muncul sekaligus, melainkan "menyapu" ruang secara bertahap mengikuti gerakan visual senjata, memberikan presisi kolisi yang jauh lebih realistis.

        Multi-Attack & Animasi Independen (list-based):
        Serangan dikelola menggunakan list active_attack sebagai kontainer objek data mandiri. Setiap serangan dalam list memiliki lifecycle sendiri. Serangan bisa tetap aktif di arena (lingering) meskipun karakter sudah berpindah ke state lain (lari/lompat), memberikan gameplay yang lebih cair. Sistem secara otomatis menghapus objek serangan dari list segera setelah durasi atau frame animasi terakhir tercapai, menjaga efisiensi penggunaan memori (RAM).

3. Manajemen Aset yang Efisien
    Sistem Image Cache: Terdapat fungsi image_cache yang berfungsi untuk mencegah pemuatan ulang file .png yang sama berkali-kali. Hal ini secara drastis mengurangi penggunaan memori dan mencegah terjadinya stuttering atau patah-patah saat game berjalan.