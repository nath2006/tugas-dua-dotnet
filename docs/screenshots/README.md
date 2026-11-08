# Indeks screenshot IF133 P6

16 screenshot dari aplikasi **Postman Desktop asli**, ditambah satu screenshot Swagger runtime. Tidak ada screenshot hasil render laporan HTML.

| No. | Bukti | Berkas |
|---|---|---|
| 01 | Collection Runner: 65 passed, 0 failed | [PNG](postman/01-postman-runner-summary.png) |
| 02 | PATCH tidak didukung: ProblemDetails 405 | [PNG](postman/02-postman-method-405.png) |
| 03 | Login Admin 200, salah 401, input invalid 400 | [PNG](postman/03-postman-login-tests.png) |
| 04 | Tanpa token: respons ProblemDetails 401 | [PNG](postman/04-postman-unauthorized-401.png) |
| 05 | POST valid:201 dengan DTO produk ID17 | [PNG](postman/05-postman-create-201.png) |
| 06 | GET detail produk:200 | [PNG](postman/06-postman-get-detail-200.png) |
| 07 | PUT valid:204 body kosong | [PNG](postman/07-postman-update-204.png) |
| 08 | GET setelah PUT:200 nama dan stok diperbarui | [PNG](postman/08-postman-verify-update-200.png) |
| 09 | Nama kosong:400 dengan errors dan traceId | [PNG](postman/09-postman-validation-400.png) |
| 10 | Token Reader tidak boleh POST:403 | [PNG](postman/10-postman-reader-forbidden-403.png) |
| 11 | GET semua produk:200 array DTO | [PNG](postman/11-postman-get-all-200.png) |
| 12 | Origin5173:204 dengan Access-Control-Allow-Origin | [PNG](postman/12-postman-cors-allowed.png) |
| 13 | Origin9999:204 tanpa Access-Control-Allow-Origin | [PNG](postman/13-postman-cors-denied.png) |
| 14 | Instance fault terisolasi:500 ProblemDetails generik tanpa stack trace | [PNG](postman/14-postman-server-error-500.png) |
| 15 | DELETE hanya produk uji:204 body kosong | [PNG](postman/15-postman-delete-204.png) |
| 16 | GET setelah DELETE:404 ProblemDetails dan traceId | [PNG](postman/16-postman-deleted-not-found-404.png) |

## Bukti tambahan dan cara membaca

- [Swagger runtime asli](00-swagger-runtime.png): dokumentasi endpoint dan Authorize.
- [Manifest Postman](postman/manifest.json): sumber dan waktu capture. collectionCases merujuk urutan collection utama, bukan ID skenario Python.
- Gambar 01–04 berasal dari hasil Collection Runner; gambar 05–16 memperlihatkan respons request langsung. Login ditampilkan melalui hasil tes, bukan body JWT.
- Gambar 12–13 menampilkan header CORS: penolakan dibuktikan oleh tidak adanya Access-Control-Allow-Origin, bukan status 403.
- Error 500 diuji pada proses fault terpisah. Tidak mematikan database pengguna.
- Screenshot tidak menggantikan rekaman lengkap 54 skenario dalam [JSON pengujian](../test-results/api-results.json).
- [Bukti read-back setelah GUI Postman](../test-results/postman-data-preservation.json) memastikan produk awal tidak berubah dan fixture sudah dihapus.
