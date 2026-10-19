# IF133 - Tugas 1

## Identitas
- Nama: Anathapindika Surja Putra
- Kelas: INFORMATIKA (EKSEKUTIF)

## Studi Kasus
Resource Product (manajemen produk/inventory) dengan field Id, Name, Description, Price, Stock.

## Teknologi
- ASP.NET Core Web API (controller)
- Entity Framework Core
- MySQL (Laragon) dengan provider Pomelo

## Cara Menjalankan
1. Jalankan Laragon, klik Start All (MySQL aktif di port 3306)
2. `dotnet restore`
3. `dotnet ef database update --project IF133.Tugas1.Api`
4. `dotnet run --project IF133.Tugas1.Api`
5. Buka https://localhost:<port>/swagger

## Endpoint
| Method | Endpoint | Keterangan |
|---|---|---|
| GET | /api/products | Ambil semua |
| GET | /api/products/{id} | Ambil satu |
| POST | /api/products | Tambah |
| PUT | /api/products/{id} | Ubah |
| DELETE | /api/products/{id} | Hapus |

## Bukti Pengujian
(tabel skenario + screenshot)

## Kendala dan Solusi
(minimal satu kendala teknis yang kamu alami)