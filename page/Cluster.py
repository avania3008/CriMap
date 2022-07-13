import time
import os
import tempfile
import base64
from typing import final
import uuid
import re
import streamlit as st
import numpy as np
import pandas as pd
import geopandas as gpd
import math
import folium
from streamlit_folium import folium_static
import folium.plugins as fp
from st_aggrid import AgGrid
from sklearn.preprocessing import StandardScaler
from pyclustering.cluster.elbow import elbow
from pyclustering.cluster.clarans import clarans
from pyclustering.utils import timedcall
import plotly.express as px
import streamlit.components.v1 as components
import page.Map as Map
import jinja2
from pretty_html_table import build_table
from zipfile import ZipFile

temp_path = tempfile.gettempdir()

geodf = gpd.read_file(r"data/Indonesia_Kab_Kota.zip")

def show_map(df, code_col, data_info, features, crime):
    java_geodf = geodf[geodf["PROVINSI"].isin(["DKI JAKARTA","JAWA BARAT","JAWA TENGAH","DAERAH ISTIMEWA YOGYAKARTA","JAWA TIMUR","BANTEN"])]
    java_geodf[code_col] = java_geodf["PROVNO"] + java_geodf["KABKOTNO"]
    java_geodf = java_geodf[[code_col,"geometry"]]
    java_geodf = java_geodf.to_crs(epsg=3035)

    x_map = java_geodf.centroid.to_crs(epsg=4326).x.mean()
    y_map = java_geodf.centroid.to_crs(epsg=4326).y.mean()
    
    df[code_col] = df[code_col].astype("int64")
    java_geodf[code_col] = java_geodf[code_col].astype("int64")

    merged = pd.merge(java_geodf, df, how="right", on=code_col)
    merged = merged.rename(columns={code_col:"KODE"})
    
    mymap = Map.initialize_map(x_map, y_map)

    folium.TileLayer(tiles="stamen terrain", name="Stamen Terrain", show=True).add_to(mymap)
    folium.TileLayer(tiles="cartodb positron", name="CartoDB (Positron)").add_to(mymap)
    folium.TileLayer(tiles="openstreetmap", name="OpenStreetMap").add_to(mymap)

    crime_layer = Map.addChoroLayer(mymap, merged, "Cluster Indikator Kriminalitas", merged, ["KODE", "Crime Cluster"], key_on="feature.properties.KODE", fill_color="YlOrRd", fill_opacity=0.8, legend_name="Crime Cluster")
    all_layer = Map.addChoroLayer(mymap, merged, "Cluster Indikator Kriminalitas & Lainnya", merged, ["KODE", "All Cluster"], key_on="feature.properties.KODE", fill_color="YlOrRd", fill_opacity=0.8, legend_name="All Cluster", show=False)

    # Map.hideColorScale(crime_layer, mymap)
    # Map.hideColorScale(all_layer, mymap)

    style_function = lambda x: {'fillColor': '#ffffff', 
                            'color':'#000000', 
                            'fillOpacity': 0.1, 
                            'weight': 0.1}
    highlight_function = lambda x: {'fillColor': '#000000', 
                                    'color':'#000000', 
                                    'fillOpacity': 0.50, 
                                    'weight': 0.1}

    list_crime_tooltip = list(np.append(data_info, np.append(crime, ["Crime Cluster"])))
    list_all_tooltip = list(np.append(data_info, np.append(features, ["All Cluster"])))
    
    crime_maps = folium.features.GeoJson(
        merged,
        style_function=style_function, 
        control=False,
        highlight_function=highlight_function, 
        tooltip=folium.features.GeoJsonTooltip(
            fields=list_crime_tooltip,
            style=("background-color: white; color: #333333; font-family: arial; font-size: 12px; padding: 10px;") 
        )
    )

    all_maps = folium.features.GeoJson(
        merged,
        style_function=style_function, 
        control=False,
        highlight_function=highlight_function, 
        tooltip=folium.features.GeoJsonTooltip(
            fields=list_all_tooltip,
            style=("background-color: white; color: #333333; font-family: arial; font-size: 12px; padding: 10px;") 
        )
    )
    crime_layer.add_child(crime_maps)
    all_layer.add_child(all_maps)

    fp.Geocoder(collapsed=True, position='topright').add_to(mymap)
    folium.LayerControl().add_to(mymap)
    fp.Fullscreen(title='Masuk mode layar penuh', title_cancel='Keluar mode layar penuh', force_separate_button=True).add_to(mymap)
    fp.LocateControl().add_to(mymap)
    fp.MousePosition(separator=' | ', num_digits=4, prefix='Koordinat').add_to(mymap)
    fp.MiniMap(tile_layer="Stamen Terrain", zoom_animation=True, toggle_display=True).add_to(mymap)
    fp.ScrollZoomToggler().add_to(mymap)
    return mymap

def num_clust(data_scaled, min_k = 2, max_k = 10):
    elbow_data = elbow(np.array(data_scaled), min_k, max_k)
    elbow_data.process()
    return elbow_data.get_amount()

def clustering(df, features, crime, mode, mn_all=5, nl_all=2, mn_crime=5, nl_crime=2):
    # try:
    # standardize the data
    features_scaled = StandardScaler().fit_transform(df[features])
    crime_scaled = StandardScaler().fit_transform(df[crime])
    # get k parameter
    k_all = num_clust(features_scaled)
    k_crime = num_clust(crime_scaled)
    # parameters
    if mode == "Parameter sudah ditentukan":
        n = df.shape[0]
        # numlocal = 2
        all_nl, crime_nl = 2, 2
        # 1.25% * k * (n-k)
        all_mn = math.ceil((1.25/100)*k_all*(n-k_all))
        crime_mn = math.ceil((1.25/100)*k_crime*(n-k_crime))
    elif mode == "Menentukan parameter sendiri":
        all_mn, all_nl, crime_mn, crime_nl = mn_all, nl_all, mn_crime, nl_crime
    # clarans clustering
    clarans_all = clarans(features_scaled.tolist(), k_all, all_nl, all_mn)
    (tks_all, res_all) = timedcall(clarans_all.process)
    clarans_crime = clarans(crime_scaled.tolist(), k_crime, crime_nl, crime_mn)
    (tks_crime, res_crime) = timedcall(clarans_crime.process)
    # indexes for each cluster
    cluster_all = clarans_all.get_clusters()
    cluster_crime = clarans_crime.get_clusters()
    # medoids
    medoids_all = clarans_all.get_medoids()
    medoids_crime = clarans_crime.get_medoids()
    # cluster result
    new_df = df.copy()
    new_df["All Cluster"] = 0
    for k in range(0, k_all):
        new_df.iloc[cluster_all[k], new_df.columns.get_loc("All Cluster")] = k+1
    new_df["Crime Cluster"] = 0
    for k in range(0, k_crime):
        new_df.iloc[cluster_crime[k], new_df.columns.get_loc("Crime Cluster")] = k+1
    return k_all, k_crime, medoids_all, medoids_crime, new_df
    # except:
    #     st.error("Terjadi suatu kesalahan")
    #     st.stop()

def visualize_clusters(df, mode):
    if mode == "All":
        clust = "All Cluster"
    elif mode == "Crime":
        clust = "Crime Cluster"

    fig = px.parallel_coordinates(df, color=clust, color_continuous_scale=px.colors.sequential.Jet)
    return fig 

def get_summary_table(table, cluster_col):
    dframe = pd.DataFrame(table)
    table_new = pd.DataFrame()
    for cl in np.unique(dframe[cluster_col]):
        table = dframe[dframe[cluster_col] == cl].describe().round(3).drop(columns=cluster_col).transpose().reset_index().rename(columns={"index":"Indicators"})
        table["Cluster"] = cl
        table_new = pd.concat([table_new, table], axis=0)
    pivot = pd.pivot_table(table_new, index=["Cluster","Indicators"])
    return pivot

def delete_results():
    if os.path.exists(f'{temp_path}\CriMap_Peta_Kriminalitas.html'):
        os.remove(f'{temp_path}\CriMap_Peta_Kriminalitas.html')
    if os.path.exists(f'{temp_path}\CriMap_Hasil_Cluster.html'):
        os.remove(f'{temp_path}\CriMap_Hasil_Cluster.html')
    if os.path.exists(f'{temp_path}\CriMap_Tabel_Cluster.csv'):
        os.remove(f'{temp_path}\CriMap_Tabel_Cluster.csv')
    if os.path.exists(f'{temp_path}\CriMap_Hasil_Clustering_dan_Peta.zip'):
        os.remove(f'{temp_path}\CriMap_Hasil_Clustering_dan_Peta.zip')

def main():
    st.markdown("<h2 style='text-align: center; color:#3E3636;'><i>Clustering</i><br>Data Baru</h2>", unsafe_allow_html=True)
    if "raw_file" not in st.session_state:
        st.session_state["raw_file"] = "data/java_crime_2020.csv"

    if "raw_df" not in st.session_state:
        st.session_state["raw_df"] = pd.read_csv(st.session_state["raw_file"])

    file_uploaded = st.file_uploader("Anda dapat menggunakan data yang sudah tersedia (tahun 2020) atau mengunggah data Anda sendiri", type=["csv"], accept_multiple_files=False, key="file_upload")
    if st.session_state["file_upload"]:  
        st.session_state["raw_df"] = pd.read_csv(st.session_state["file_upload"])
        st.session_state["raw_file"] = file_uploaded.name
        st.success("Berhasil mengunggah data!")
    st.info("Data saat ini : {}".format(st.session_state["raw_file"]))
    
    st.markdown("<h4 style='text-align: center; color:#3E3636;'>Tabel Data</h4>", unsafe_allow_html=True)
    raw_df = st.session_state["raw_df"]
    df = AgGrid(raw_df, editable=True)['data']
    df = df.fillna(0)
    st.session_state["raw_df"] = df
    
    st.markdown("<h4 style='text-align: center; color:#3E3636;'>Pengaturan <i>Clustering</i></h4>", unsafe_allow_html=True)
    idcol, datainfo = st.columns([4,4])
    id_col = idcol.selectbox("Pilih kolom kode wilayah", df.columns, help="Format kode wilayah untuk tingkat Kabupaten/Kota terdiri dari 4 angka (2 angka kode tingkat provinsi dan 2 angka kode tingkat kabupaten/kota). Contohnya: Kabupaten Kepulauan Seribu kode wilayahnya 3101 (31 kode tingkat provinsi & 01 kode tingkat kabupaten/kota)")
    data_info = datainfo.multiselect("Pilih kolom nama wilayah", df.loc[:,df.columns!=id_col].select_dtypes(include=['object']).columns, help="Nama wilayah bisa berupa nama provinsi dan atau nama kabupaten/kota")
    if not data_info:
        st.info("Dimohon memilih kolom yang digunakan untuk nama wilayah")
    else:
        all_col, crime_col = st.columns([4,4])
        with all_col:
            features = st.multiselect("Pilih kolom-kolom indikator (termasuk indikator kriminalitas)", df.loc[:,df.columns!=id_col].select_dtypes(include=['float64','int64']).columns,
                                        help="Pilih semua kolom / variabel / indikator yang akan digunakan untuk analisis cluster")
            if features:
                with crime_col:
                    crime = st.multiselect("Pilih indikator kriminalitas", df[features].columns, help="Pilih beberapa kolom / variabel / indikator yang sebelumnya sudah dipilih sebagai indikator kriminalitas")
    
        if not features:
            st.info("Dimohon memilih setidaknya satu kolom / variabel / indikator yang tersedia dari dataset")
        elif not crime:
            st.info("Dimohon memilih setidaknya satu kolom / variabel / indikator dari kolom terpilih sebelumnya sebagai indikator kriminalitas")
        elif features and crime:
            param_mode = st.radio("Pengaturan parameter clustering",["Parameter sudah ditentukan","Menentukan parameter sendiri"])
            if param_mode == "Menentukan parameter sendiri":
                col1, col2, col3, col4 = st.columns([2,2,2,2])
                mn_all = col1.number_input("MaxNeighbor (Kriminalitas & Lainnya)",value=5, min_value=1, help="Maxneighbor atau jumlah data point berdekatan yang akan dianalisa (untuk clustering indikator kriminalitas dan indikator lainnya")                    
                nl_all = col2.number_input("NumLocal (Kriminalitas & Lainnya)",value=2, min_value=1, help="Numlocal atau jumlah iterasi yang ingin dicapai sampai mendapatkan hasil analisa cluster (untuk clustering indikator kriminalitas dan indikator lainnya")
                mn_crime = col3.number_input("MaxNeighbor (Kriminalitas)",value=5, min_value=1, help="Maxneighbor atau jumlah data point berdekatan yang akan dianalisa (untuk clustering indikator kriminalitas saja")
                nl_crime = col4.number_input("NumLocal (Kriminalitas)",value=2, min_value=1, help="Numlocal atau jumlah iterasi yang ingin dicapai sampai mendapatkan hasil analisa cluster (untuk clustering indikator kriminalitas saja")
            st.success("Siap melakukan analisis cluster")
            cls_button = st.button("Lakukan Clustering")
            if cls_button:
                lf, md, rt = st.columns(3)
                gif_runner = md.image("img/loading.gif", use_column_width=True)
                delete_results()
                if param_mode == "Parameter sudah ditentukan":
                    all_k, crime_k, all_meds, crime_meds, new_df = clustering(st.session_state["raw_df"], features, crime, param_mode)
                elif param_mode == "Menentukan parameter sendiri":
                    all_k, crime_k, all_meds, crime_meds, new_df = clustering(st.session_state["raw_df"], features, crime, param_mode, mn_all, nl_all, mn_crime, nl_crime)                                                                                                                                                           
                gif_runner.empty()
                st.markdown("<h2 style='text-align: center; color:#3E3636;'>Hasil Analisis <i>Cluster</i></h2>", unsafe_allow_html=True)
                all_res_table = new_df[np.concatenate((data_info, features, ["All Cluster"]))]
                crime_res_table = new_df[np.concatenate((data_info, crime, ["Crime Cluster"]))]
                
                with st.expander("Detail Analisis Cluster dengan Indikator Kriminalitas & Lainnya"):
                    st.markdown("<strong style='color:#3E3636;'>Jumlah <i>cluster</i> :</strong>&nbsp;{}".format(all_k), unsafe_allow_html=True)
                    st.markdown("<strong style='color:#3E3636;'><i>Cluster medoids</i> :</strong>", unsafe_allow_html=True)
                    st.dataframe(all_res_table.iloc[all_meds,:].drop(columns=data_info))
                    st.markdown("<strong style='color:#3E3636;'>Hasil <i>cluster</i> :</strong>", unsafe_allow_html=True)
                    AgGrid(all_res_table)
                    st.markdown("<strong style='color:#3E3636;'>Visualisasi hasil CLARANS <i>clustering</i></strong>", unsafe_allow_html=True)
                    st.plotly_chart(visualize_clusters(all_res_table , "All"), use_container_width=True)
                    st.markdown("<strong style='color:#3E3636;'>Statistik Deskriptif</strong>", unsafe_allow_html=True)
                    pivot_all = get_summary_table(all_res_table,"All Cluster")
                    AgGrid(pivot_all.reset_index())
                with st.expander("Detail Analisis Cluster dengan Indikator Kriminalitas"):
                    st.markdown("<strong style='color:#3E3636;'>Jumlah <i>cluster</i> :</strong>&nbsp;{}".format(crime_k), unsafe_allow_html=True)
                    st.markdown("<strong style='color:#3E3636;'><i>Cluster medoids</i> :</strong>", unsafe_allow_html=True)
                    st.dataframe(crime_res_table.iloc[crime_meds,:].drop(columns=data_info))
                    st.markdown("<strong style='color:#3E3636;'>Hasil <i>cluster</i> :</strong>", unsafe_allow_html=True)
                    AgGrid(crime_res_table)
                    st.markdown("<strong style='color:#3E3636;'>Visualisasi hasil CLARANS <i>clustering</i></strong>", unsafe_allow_html=True)
                    st.plotly_chart(visualize_clusters(crime_res_table, "Crime"), use_container_width=True)
                    st.markdown("<strong style='color:#3E3636;'>Statistik Deskriptif</strong>", unsafe_allow_html=True)
                    pivot_crime = get_summary_table(crime_res_table,"Crime Cluster")
                    AgGrid(pivot_crime.reset_index())

                with st.spinner("Harap menunggu sebentar untuk merangkum hasil analisis dan memuat tombol Simpan Hasil"):
                    time.sleep(15)
                lf2, md2, rt2 = st.columns(3)
                gif_runner2 = md2.image("img/loading.gif", use_column_width=True)
                # create and save map
                new_map = show_map(new_df, id_col, data_info, features, crime)
                new_map.save(f"{temp_path}\CriMap_Peta_Kriminalitas.html")

                # read result template
                template_dir = "template/"
                env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir))
                res_template = env.get_template("cluster_result.html")

                # write results to template
                with open(f"{temp_path}\CriMap_Hasil_Cluster.html","w") as results:
                    results.write(res_template.render(
                        all_k=all_k,
                        all_meds_table= build_table(all_res_table.iloc[all_meds,:].drop(columns=data_info), "grey_dark", padding="10px", font_family="serif"),
                        all_res_table= build_table(all_res_table,"grey_dark", padding="10px", font_family="serif"),
                        all_vis=visualize_clusters(all_res_table , "All").to_html(full_html=False),
                        all_summary= build_table(pivot_all.reset_index(),"grey_dark", padding="10px", font_family="serif"),
                        crime_k=crime_k,
                        crime_meds_table= build_table(crime_res_table.iloc[crime_meds,:].drop(columns=data_info),"grey_dark", padding="10px", font_family="serif"),
                        crime_res_table= build_table(crime_res_table,"grey_dark", padding="10px", font_family="serif"),
                        crime_vis=visualize_clusters(crime_res_table, "Crime").to_html(full_html=False),
                        crime_summary= build_table(pivot_crime.reset_index(),"grey_dark", padding="10px", font_family="serif")
                    ))

                # csv output
                new_df[np.concatenate((data_info,features,["All Cluster","Crime Cluster"]))].to_csv(f"{temp_path}\CriMap_Tabel_Cluster.csv")
                
                # zip folder output
                output_file = f"{temp_path}\CriMap_Hasil_Clustering_dan_Peta.zip"
                zip_files = ZipFile(output_file,'w')
                zip_files.write(f"{temp_path}\CriMap_Peta_Kriminalitas.html", os.path.basename(f"{temp_path}\CriMap_Peta_Kriminalitas.html"))
                zip_files.write(f"{temp_path}\CriMap_Hasil_Cluster.html", os.path.basename(f"{temp_path}\CriMap_Hasil_Cluster.html"))
                zip_files.write(f"{temp_path}\CriMap_Tabel_Cluster.csv", os.path.basename(f"{temp_path}\CriMap_Tabel_Cluster.csv"))
                zip_files.close()
                
                file_size = os.path.getsize(output_file)
                file_size_mb = round(file_size/(1024*1024), 2)
                dwl_label = f"Simpan Hasil ({file_size_mb} MB)"
                
                with open(output_file, 'rb') as f:
                    b64 = base64.b64encode(f.read()).decode('utf8')

                button_uuid = str(uuid.uuid4()).replace('-', '')
                button_id = re.sub('\d+', '', button_uuid)

                custom_css = f""" 
                    <style>
                        #{button_id} {{
                            background-color: rgb(255, 255, 255);
                            color: rgb(38, 39, 48);
                            padding: 0.25em 0.38em;
                            position: relative;
                            text-decoration: none;
                            border-radius: 4px;
                            border-width: 1px;
                            border-style: solid;
                            border-color: rgb(230, 234, 241);
                            border-image: initial;
                        }} 
                        #{button_id}:hover {{
                            border-color: rgb(246, 51, 102);
                            color: rgb(246, 51, 102);
                        }}
                        #{button_id}:active {{
                            box-shadow: none;
                            background-color: rgb(246, 51, 102);
                            color: white;
                            }}
                    </style> """
                
                dl_link = custom_css + f'<a download="CriMap_Hasil_Clustering_dan_Peta.zip" id="{button_id}" href="data:application/zip;base64,{b64}">{dwl_label}</a><br></br>'
                
                st.warning("PERHATIAN!! Jangan lupa untuk menyimpan hasil saat ini dengan menekan tombol 'Simpan Hasil' sebelum menekan kembali tombol 'Lakukan Clustering' untuk melakukan analisis ulang.")
                gif_runner2.empty()
                st.markdown(dl_link, unsafe_allow_html=True)
                
