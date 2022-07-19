import streamlit as st
import base64

def show_gif(img_url):
    gif = open(img_url, "rb")
    contents = gif.read()
    data_url = base64.b64encode(contents).decode("utf-8")
    gif.close()
    return data_url

def map_info():
    st.markdown(f'''
        <h4 style='color:#3E3636;'><u>Halaman Peta</u></h4>
        <div>
            <p>Pada halaman ini akan ditampilkan :</p>
            <ol>
                <li>
                    <p><u>Peta kriminalitas untuk kabupaten/kota di Pulau Jawa tahun 2020 yang interaktif.</u><br>Pengguna dapat menganti <i>base map</i> dan juga menampilkan/menyembunyikan <i>layer cluster</i>. Selain itu,
                    pengguna peta dapat melihat informasi masing-masing kabupaten/kota dengan mengarahkan kursor ke wilayah yang dituju</p>
                    <img class="gif" src="data:image/gif;base64,{show_gif("img/interactive_map.gif")}" alt="Peta Interaktif">
                    <br>
                </li>
                <li><p><u>Detail data yang digunakan dan visualisasi data mentah.</u><br>Detail dan visualisasi data berupa tabel data hasil <i>clustering</i>, keterangan kolom pada tabel, nilai statistik deskriptif, plot korelasi, dan histogram</p></li>
                <li>
                    <p><u>Detail dan visualisasi hasil analisis <i>cluster</i></u><br>
                    Terdapat visualisasi data hasil analisis <i>cluster</i> berupa <i>paralel coordinates</i> yang interaktif dan keterangan karakteristik dari masing-masing <i>cluster</i></p>
                    <img class="gif" src="data:image/gif;base64,{show_gif("img/interactive_parcoord.gif")}" alt="Visualisasi Data Interaktif">
                </li>
            </ol>
        </div>
        ''', unsafe_allow_html=True)

def clust_info():
    st.markdown(f'''
        <h4 style='color:#3E3636;'><u>Halaman <i>Clustering</i></u></h4>
        <div>
            <p style="text-align: justify;">Halaman ini digunakan untuk melakukan analisis <i>cluster</i> dengan algoritma <i>Clustering Large Applications based on RANdomized Search</i> (CLARANS) 
            menggunakan data yang sudah tersedia (tahun 2020) atau pengguna dapat mengunggah data terbaru yang ingin dianalisis.</p>
            <ol>
                <li>
                    <p>Data yang akan digunakan akan ditampilkan terlebih dahulu dalam bentuk tabel data yang interaktif (bisa melakukan <i>edit</i> data langsung pada tabel)</p>
                    <img class="gif" src="data:image/gif;base64,{show_gif("img/interactive_table.gif")}" alt="Tabel Data Interaktif">
                    <br>
                </li>
                <li>
                    <p>Selanjutnya pengguna akan diminta untuk memberikan beberapa <i>input</i> yang dibutuhkan seperti :</p>
                    <p>&bull;&nbsp;<strong>Kolom kode wilayah</strong>&nbsp;:&nbsp;sebuah kolom yang berisikan data kode wilayah sampai ke tingkat kabupaten/kota (4 digit angka)</p>
                    <p>&bull;&nbsp;<strong>Kolom nama wilayah</strong>&nbsp;:&nbsp;satu atau lebih kolom yang merepresentasikan nama wilayah</p>
                    <p>&bull;&nbsp;<strong>Kolom semua indikator</strong>&nbsp;:&nbsp;satu atau lebih kolom yang akan dianalisis, termasuk data indikator kriminalitas (data numerik)</p>
                    <p>&bull;&nbsp;<strong>Kolom indikator kriminalitas</strong>&nbsp;:&nbsp;satu atau lebih kolom yang merupakan indikator kriminalitas (data numerik)</p>
                    <p>&bull;&nbsp;<strong>Parameter <i>clustering</i></strong>&nbsp;:&nbsp;pengguna dapat memilih jika parameter ingin ditentukan oleh aplikasi atau menentukan parameternya sendiri</p>
                    <p>Jika pengguna memilih untuk menentukan parameter sendiri, maka parameter yang perlu diberikan untuk masing-masing analisis (indikator kriminalitas & lainnya dan indikator kriminalitas saja) antara lain :</p>
                    <p>&bull;&nbsp;<strong><i>MaxNeighbor</i></strong>&nbsp;:&nbsp;jumlah <i>data point</i> berdekatan yang akan dianalisis</p>
                    <p>&bull;&nbsp;<strong><i>NumLocal</i></strong>&nbsp;:&nbsp;jumlah iterasi yang dilakukan untuk memperoleh hasil akhir</p>
                </li>
                <li>
                    <p>Jika semua <i>input</i> sudah dilengkapi maka pengguna dapat melakukan proses analisis <i>cluster</i> dengan menekan tombol <strong>Lakukan Clustering</strong>. 
                    Analisis yang dilakukan akan menggunakan tabel data pada langkah nomor 1 (jika dilakukan <i>editing</i> pada tabel data, maka proses analisis akan menggunakan data terbaru yang sudah di-<i>edit</i>)</p>
                </li>
                <li>
                    <p>Setelah menunggu beberapa saat, pengguna dapat melihat hasil analisis <i>cluster</i> dan peta <i>choropleth</i> berdasarkan nomor <i>cluster</i>, serta dapat menyimpan hasil analisis dan peta tersebut dengan menekan tombol <strong>Simpan Hasil</strong>. Hasil analisis yang tersimpan akan berupa <i>file .zip</i> yang berisikan 3 macam <i>file</i> :</p>
                    <p>&bull;&nbsp;<strong>CriMap_Hasil_Cluster.html</strong>&nbsp;:&nbsp;hasil detail analisis secara keseluruhan (visualisasi hasil analisis interaktif)</p>
                    <p>&bull;&nbsp;<strong>CriMap_Peta_Kriminalitas.html</strong>&nbsp;:&nbsp;hasil peta kriminalitas (interaktif)</p>
                    <p>&bull;&nbsp;<strong>CriMap_Tabel_Cluster.csv</strong>&nbsp;:&nbsp;hanya tabel data hasil nomor <i>cluster</i></p>
                </li>
            </ol>
        </div>
        ''', unsafe_allow_html=True)

def main():
    st.markdown("<h1 style='text-align: center; color:#3E3636;'>Selamat datang di <i>Website</i></h1>", unsafe_allow_html=True)
    st.write("\n\n\n")
    col1, col2, col3 = st.columns([2.5,3,2.5])
    with col1:
        st.write("")
    with col2:
        st.image('img/crimap-logo.png', use_column_width=True)
    with col3:
        st.write("")
    st.write("\n\n\n")
    st.markdown("<h3 style='text-align: center; color:#3E3636;'>Aplikasi Pemetaan Kriminalitas Kabupaten/Kota di Pulau Jawa<br>menggunakan Algoritma CLARANS</h3><br>", unsafe_allow_html=True)
    st.markdown('''
    <div class="bg-div">
        <h2>Latar Belakang</h2>
        <p>
            Kriminalitas adalah salah satu masalah sosial yang menjadi perhatian di Indonesia. Salah satu faktor yang mempengaruhi tingkat kriminalitas di Indonesia adalah kepadatan penduduk,
            di mana kepadatan penduduk tertinggi untuk negara Indonesia berada di Pulau Jawa. Analisis pengelompokkan atau analisis <i>cluster</i> dilakukan untuk mengelompokkan dan mengetahui 
            tingkat kriminalitas dari masing-masing wilayah di Pulau Jawa, khususnya pada tingkat kabupaten/kota. Pengunaan algoritma CLARANS dipertimbangkan karena merupakan algoritma <i>clustering</i> 
            partisi yang cukup efektif dan efisien dibandingkan dengan metode-metode partisi pendahulunya.
        </p>
    </div>

    ''', unsafe_allow_html=True)

    obj, ben = st.columns(2)

    with obj.expander("Tujuan"):    
        st.markdown('''
            <p>&bull;&nbsp;Mencari tahu kelompok tingkat kriminalitas dari tiap kabupaten dan kota di Pulau Jawa, Indonesia</p>
            <p>&bull;&nbsp;Mendapatkan gambaran mengenai karakteristik tiap kelompok kabupaten dan kota yang terbentuk</p>
            <p>&bull;&nbsp;Menyajikan visualisasi hasil analisis pengelompokkan berupa peta <i>choropleth</i></p>
        ''', unsafe_allow_html=True)
    
    with ben.expander("Manfaat"):
        st.markdown('''
            <p>&bull;&nbsp;Mengetahui faktor-faktor kriminalitas dan faktor sosial lain yang bermasalah dan perlu diperhatikan untuk masing-masing kelompok wilayah</p>
            <p>&bull;&nbsp;Mempermudah pengguna <i>website</i> CriMap untuk melakukan analisis dan pemantauan tingkat kriminalitas dari kabupaten dan kota di Pulau Jawa, Indonesia</p>
        ''', unsafe_allow_html=True)

    st.markdown("<br><h2 style='text-align: center; color:#3E3636;'>Halaman-Halaman pada Aplikasi</h2>", unsafe_allow_html=True)
    pages = st.radio("Pilih halaman yang ingin diketahui informasinya",["Peta", "Clustering"])
    if pages == "Peta":
        map_info()
    elif pages == "Clustering":
        clust_info()
        st.warning("**PERINGATAN!!!** Setelah pengguna menekan tombol *Lakukan Clustering* untuk melakukan analisis ulang maka hasil analisis saat itu akan langsung terhapus")
    
