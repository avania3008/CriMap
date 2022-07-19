import streamlit as st
import tempfile
import geopandas as gpd
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from st_aggrid import AgGrid
import folium
import folium.plugins as fp
import branca.colormap as cmp
import base64
import minify_html
import streamlit.components.v1 as components
from html2image import Html2Image
from PIL import Image

temp_path = tempfile.gettempdir()

geodf = gpd.read_file(r"data/Indonesia_Kab_Kota.zip")
df = pd.read_csv("data/cluster_final_result.csv")

def initialize_map(x, y):
    map = folium.Map(location=[y, x], zoom_start=7, tiles=None, prefer_canvas=True)
    return map

def addChoroLayer(m, geo_data, name, data, columns, key_on, legend_name=None, fill_color=None, fill_opacity=None, line_opacity=0.5, smooth_factor=0, show=True):
    return folium.Choropleth(geo_data=geo_data, name=name, data=data, columns=columns, key_on=key_on, legend_name=legend_name, fill_color=fill_color, fill_opacity=fill_opacity,
                            line_opacity=line_opacity, smooth_factor=smooth_factor, show=show).add_to(m)

def hideColorScale(layer, m):
    for key in layer._children:
        if key.startswith('color_map'):
            del(layer._children[key])
    layer.add_to(m)

def create_map():
    # select java from geodf
    java_geodf = geodf[geodf["PROVINSI"].isin(["DKI JAKARTA","JAWA BARAT","JAWA TENGAH","DAERAH ISTIMEWA YOGYAKARTA","JAWA TIMUR","BANTEN"])]

    # add attribute "Kode Wilayah"
    java_geodf["Kode Wilayah"] = java_geodf["PROVNO"] + java_geodf["KABKOTNO"]
    java_geodf = java_geodf[["Kode Wilayah","geometry"]]
    java_geodf = java_geodf.to_crs(epsg=3035)

    # map center
    x_map = java_geodf.centroid.to_crs(epsg=4326).x.mean()
    y_map = java_geodf.centroid.to_crs(epsg=4326).y.mean()
    
    # join table
    df["Kode Wilayah"] = df["Kode Wilayah"].astype("int64")
    java_geodf["Kode Wilayah"] = java_geodf["Kode Wilayah"].astype("int64")
    merged = pd.merge(java_geodf, df, how="right", on="Kode Wilayah")
    merged = merged.rename(columns={"Kode Wilayah":"KODE"})
    
    # map initialization
    mymap = initialize_map(x_map, y_map)

    # add tile layer options
    folium.TileLayer(tiles="stamen terrain", name="Stamen Terrain", show=True).add_to(mymap)
    folium.TileLayer(tiles="cartodb positron", name="CartoDB (Positron)").add_to(mymap)
    folium.TileLayer(tiles="openstreetmap", name="OpenStreetMap").add_to(mymap)

    # add choropleth layer
    crime_layer = addChoroLayer(mymap, merged, "Cluster Indikator Kriminalitas", merged, ["KODE", "Cl Crime"], key_on="feature.properties.KODE")
    all_layer = addChoroLayer(mymap, merged, "Cluster Indikator Kriminalitas & Lainnya", merged, ["KODE", "Cl PC1"], key_on="feature.properties.KODE", show=False)
    
    # hide color scale
    hideColorScale(crime_layer, mymap)
    hideColorScale(all_layer, mymap)

    # interactive map
    color_step = cmp.StepColormap(
      ['#E97171','#931A25','#F6E7D8','#FFB5B5'],
      vmin=1, vmax=4,
      index=[0,1,2,3,4]
    )

    crime_dict = merged.copy().set_index('KODE')['Cl Crime'].to_dict()
    all_dict = merged.copy().set_index('KODE')['Cl PC1'].to_dict()

    crime_style_function = lambda x: {'fillColor': color_step(crime_dict.get(x['properties']['KODE'])), 
                            'color':'#000000', 
                            'fillOpacity': 0.8, 
                            'weight': 0.1}
    all_style_function = lambda x: {'fillColor': color_step(all_dict.get(x['properties']['KODE'])), 
                            'color':'#000000', 
                            'fillOpacity': 0.8, 
                            'weight': 0.1}
    highlight_function = lambda x: {'fillColor': '#000000', 
                                    'color':'#000000', 
                                    'fillOpacity': 0.50, 
                                    'weight': 0.1}
    crime_maps = folium.GeoJson(
        merged,
        style_function=crime_style_function, 
        control=False,
        highlight_function=highlight_function, 
        tooltip=folium.features.GeoJsonTooltip(
            fields=['Kabupaten/Kota','CT 2020','CRR 2020','Cl Crime Name'],
            aliases=['Kabupaten/Kota','Crime Total', 'Crime Rate', 'Cluster Kriminalitas'],
            style=("background-color: white; color: #333333; font-family: arial; font-size: 12px; padding: 10px;") 
        )
    )

    all_maps = folium.GeoJson(
        merged,
        style_function=all_style_function, 
        control=False,
        highlight_function=highlight_function, 
        tooltip=folium.features.GeoJsonTooltip(
            fields=['Kabupaten/Kota','KP 2020','PPM 2020','RLS 2020','CT 2020','CRR 2020','Cl PC1 Name'],
            aliases=['Kabupaten/Kota','Kepadatan Penduduk', 'Penduduk Miskin (%)', 'Rata-rata Lama Sekolah', 'Crime Total', 'Crime Rate', 'Cluster Kriminalitas & Lainnya'],
            style=("background-color: white; color: #333333; font-family: arial; font-size: 12px; padding: 10px;") 
        )
    )
    crime_layer.add_child(crime_maps)
    all_layer.add_child(all_maps)

    # plugins
    fp.Geocoder(collapsed=True, position='topright').add_to(mymap)
    folium.LayerControl().add_to(mymap)
    fp.Fullscreen(title='Masuk mode layar penuh', title_cancel='Keluar mode layar penuh', force_separate_button=True).add_to(mymap)
    fp.LocateControl().add_to(mymap)
    fp.MousePosition(separator=' | ', num_digits=4, prefix='Koordinat').add_to(mymap)
    fp.MiniMap(tile_layer="Stamen Terrain", zoom_animation=True, toggle_display=True).add_to(mymap)
   
    # # legends (only once)
    # hti = Html2Image(output_path='img')

    # hti.screenshot(
    #   html_file='legends/legends.html', css_file='legends/legends_css.css',
    #   save_as='legends.png'
    # )  

    # crop html image
    # box = (0,0,220,300)
    # legends = Image.open("img/legends.png")
    # legends2 = legends.crop(box)
    # legends2.save("img/legends_cropped.png")

    with open("img/legends_cropped.png", 'rb') as lf:
      legend_content = base64.b64encode(lf.read()).decode('utf-8')

    fp.FloatImage('data:image/png;base64,{}'.format(legend_content), bottom=1, left=1).add_to(mymap)
    return mymap
    
def main():
    st.markdown("<h2 style='text-align: center; color:#3E3636;'>Peta Kriminalitas Tahun 2020</h2>", unsafe_allow_html=True)
    
    lf, md, rt = st.columns(3)
    gif_runner = md.image("img/loading.gif", use_column_width=True)
    if "map_2020_html" not in st.session_state:
      map_2020 = create_map()
      map_html = map_2020.get_root().render()
      minified_map = minify_html.minify(map_html)
      st.session_state["map_2020_html"] = minified_map
    components.html(st.session_state["map_2020_html"], height=500)
    gif_runner.empty()
    
    with st.expander("Tentang Data", expanded=True):
        st.markdown("<h5 style='text-align: center; color:#3E3636;'>Tabel Data</h5>", unsafe_allow_html=True)
        raw = df[["Kode Wilayah","Provinsi","Kabupaten/Kota","KP 2020","PPM 2020","RLS 2020","CT 2020","CRR 2020","Cl PC1","Cl Crime","Cl PC1 Name","Cl Crime Name"]]
        AgGrid(raw)
        st.markdown("<h5 style='text-align: center; color:#3E3636;'>Informasi Data</h5>", unsafe_allow_html=True)
        table_info, stat = st.columns(2)
        with table_info:
            st.markdown('''
            <div style="overflow-x:auto;">
              <table>
                <tr>
                  <th>Kolom</th>
                  <th>Deskripsi</th>
                </tr>
                <tr>
                  <td>Kode Wilayah</td>
                  <td>Kode wilayah resmi suatu kabupaten/kota berdasarkan <a href='https://sig.bps.go.id/bridging-kode/index'>Sistem Informasi Geografis BPS</a></td>\
                </tr>
                <tr>
                  <td>Provinsi</td>
                  <td>Nama provinsi</td>\
                </tr>
                <tr>
                  <td>Kabupaten/Kota</td>
                  <td>Nama kabupaten/kota</td>\
                </tr>
                <tr>
                  <td>KP 2020</td>
                  <td>Kepadatan penduduk tahun 2020</td>\
                </tr>
                <tr>
                  <td>PPM 2020</td>
                  <td>Persentase penduduk miskin tahun 2020</td>\
                </tr>
                <tr>
                  <td>RLS 2020</td>
                  <td>Rata-rata lama sekolah tahun 2020</td>\
                </tr>
                <tr>
                  <td>CT 2020</td>
                  <td><i>Crime total</i> atau jumlah tindak pidana tercatat tahun 2020</td>\
                </tr>
                <tr>
                  <td>CRR 2020</td>
                  <td><i>Crime rate</i> atau risiko penduduk terkena tindak kejahatan per 100.000 penduduk tahun 2020</td>\
                </tr>
                <tr>
                <tr>
                  <td>Cl PC1</td>
                  <td>Nomor <i>cluster</i> menggunakan indikator kriminalitas dan indikator lainnya</td>\
                </tr>
                <tr>
                <tr>
                  <td>Cl Crime</td>
                  <td>Nomor <i>cluster</i> menggunakan indikator kriminalitas saja</td>\
                </tr>
                <tr>
                  <td>Cl PC1 Name</td>
                  <td>Nama <i>cluster</i> menggunakan indikator kriminalitas dan indikator lainnya</td>\
                </tr>
                <tr>
                  <td>Cl Crime Name</td>
                  <td>Nama <i>cluster</i> menggunakan indikator kriminalitas saja</td>\
                </tr>
              </table>
            </div>
            ''', unsafe_allow_html=True)
            st.write("\n")
        
        with stat:
            st.selectbox("Pilih statistik",["Statistik Deskriptif","Plot Korelasi","Histogram"], key="stat")
            raw_features = raw.iloc[:,3:-4]
            if st.session_state["stat"] == "Statistik Deskriptif":
              if "describe_data" not in st.session_state:
                st.session_state["describe_data"] = raw_features.describe()
              st.write(st.session_state["describe_data"])
            elif st.session_state["stat"] == "Plot Korelasi":
              if "corr_plot" not in st.session_state:
                corr = raw_features.corr()
                st.session_state["corr_plot"] = px.imshow(corr, color_continuous_scale='RdBu_r', text_auto=True)
              st.plotly_chart(st.session_state["corr_plot"], use_container_width=True)
            elif st.session_state["stat"] == "Histogram":
              st.selectbox("Pilih indikator", raw_features.columns, key="hist_col")
              st.slider("Jumlah bin", min_value=10, max_value=100, value=20, key="hist_bins")
              hist = px.histogram(raw_features, x=st.session_state["hist_col"], 
                                  title="Histogram dari {}".format(st.session_state["hist_col"]), nbins=st.session_state["hist_bins"])
              st.plotly_chart(hist, use_container_width=True)

    with st.expander("Tentang Cluster", expanded=True):
      st.markdown("<h5 style='text-align: center; color:#3E3636;'>Visualisasi <i>Cluster</i></h5>", unsafe_allow_html=True)
      st.markdown("<strong>Indikator Kriminalitas & Lainnya</strong>", unsafe_allow_html=True)
      dim1 = list([dict(range=[df['KP 2020'].min(),df['KP 2020'].max()], 
                      tickvals=np.append(np.arange(df['KP 2020'].min(),df['KP 2020'].max(),1000),df['KP 2020'].max()),
                      label='KP', values=df['KP 2020']),
                 dict(range=[df['PPM 2020'].min(),df['PPM 2020'].max()],
                      tickvals=np.append(np.arange(df['PPM 2020'].min(),df['PPM 2020'].max(),2),df['PPM 2020'].max()),
                      label='PPM', values=df['PPM 2020']),
                 dict(range=[df['RLS 2020'].min(),df['RLS 2020'].max()],
                      tickvals=np.append(np.arange(df['RLS 2020'].min(),df['RLS 2020'].max(),1),df['RLS 2020'].max()),
                      label='RLS', values=df['RLS 2020']),
                 dict(range=[df['CT 2020'].min(),df['CT 2020'].max()],
                      tickvals=np.append(np.arange(df['CT 2020'].min(),df['CT 2020'].max(),100),df['CT 2020'].max()),
                      label='CT', values=df['CT 2020']),
                 dict(range=[df['CRR 2020'].min(),df['CRR 2020'].max()],
                      tickvals=np.append(np.arange(df['CRR 2020'].min(),df['CRR 2020'].max(),20),df['CRR 2020'].max()),
                      label='CRR', values=df['CRR 2020']),
              
                 dict(range=[df['Cl PC1'].min(), df['Cl PC1'].max()],
                      tickvals=np.unique(df['Cl PC1']),
                      label='Nomor Cluster', values=df['Cl PC1']),
                ])
      fig1 = go.Figure(data=go.Parcoords(line = dict(color = df['Cl PC1'],
               colorscale = [[0,'red'],[0.25,'green'],[0.75,'purple'],[1,'blue']]), dimensions=dim1))
      fig1.update_layout(
          title="CLARANS Clustering menggunakan Indikator Kriminalitas & Lainnya"
      )
      st.plotly_chart(fig1, use_container_width=True)

      st.markdown("<strong>Indikator Kriminalitas</strong>", unsafe_allow_html=True)
      dim2 = list([
                 dict(range=[df['CT 2020'].min(),df['CT 2020'].max()],
                      tickvals=np.append(np.arange(df['CT 2020'].min(),df['CT 2020'].max(),100),df['CT 2020'].max()),
                      label='CT', values=df['CT 2020']),
                 dict(range=[df['CRR 2020'].min(),df['CRR 2020'].max()],
                      tickvals=np.append(np.arange(df['CRR 2020'].min(),df['CRR 2020'].max(),20),df['CRR 2020'].max()),
                      label='CRR', values=df['CRR 2020']),
              
                 dict(range=[df['Cl Crime'].min(), df['Cl Crime'].max()],
                      tickvals=np.unique(df['Cl Crime']),
                      label='Nomor Cluster', values=df['Cl Crime']),
                ])
      fig2 = go.Figure(data=go.Parcoords(line = dict(color = df['Cl Crime'],
                         colorscale = [[0,'red'],[0.25,'green'],[0.75,'purple'],[1,'blue']]), dimensions=dim2))
      fig2.update_layout(
          title="CLARANS Clustering menggunakan Indikator Kriminalitas"
      )
      st.plotly_chart(fig2, use_container_width=True)

      st.markdown("<h5 style='text-align: center; color:#3E3636;'>Karakteristik <i>Cluster</i></h5>", unsafe_allow_html=True)
      char_all, char_crime = st.columns([4,4])
      with char_all :
        all_table = '''
          <div style="overflow-x:auto;">
            <table>
              <caption style="caption-side: top; text-align: center;"><i>Cluster</i> Indikator Kriminalitas & Lainnya</caption>
              <tr>
                <th>Nomor <i>Cluster</i></th>
                <th>Nama <i>Cluster</i> </th>
                <th>Karakteristik</th>
              </tr>
              <tr>
                <td>1 (merah)</td>
                <td><i>Need more attention</i><br>(Butuh perhatian lebih)</td>
                <td>
                  <ul>
                    <li>Kepadatan penduduk menengah</li>
                    <li>Persentase penduduk miskin rendah</li>
                    <li>Rata-rata lama sekolah tinggi</li>
                    <li><i>Crime total</i> menengah</li>
                    <li><i>Crime rate</i> cenderung rendah</li>
                  </ul>
                </td>\
              </tr>
              <tr>
                <td>2 (hijau)</td>
                <td><i>Need urgent attention</i><br>(Paling butuh perhatian)</td>
                <td>
                  <ul>
                    <li>Kepadatan penduduk tinggi</li>
                    <li>Persentase penduduk miskin rendah</li>
                    <li>Rata-rata lama sekolah tinggi</li>
                    <li><i>Crime total</i> tinggi</li>
                    <li><i>Crime rate</i> menengah ke atas</li>
                  </ul>
                </td>\
              </tr>
              <tr>
                <td>3 (ungu)</td>
                <td><i>Need least attention</i><br>(Paling sedikit butuh perhatian)</td>
                <td>
                  <ul>
                    <li>Kepadatan penduduk rendah</li>
                    <li>Persentase penduduk miskin menyebar</li>
                    <li>Rata-rata lama sekolah menengah</li>
                    <li><i>Crime total</i> rendah</li>
                    <li><i>Crime rate</i> rendah</li>
                  </ul>
                </td>\
              </tr>
              <tr>
                <td>4 (biru)</td>
                <td><i>Need a little attention</i><br>(Butuh sedikit perhatian)</td>
                <td>
                  <ul>
                    <li>Kepadatan penduduk menengah</li>
                    <li>Persentase penduduk miskin menengah</li>
                    <li>Rata-rata lama sekolah menengah ke atas</li>
                    <li><i>Crime total</i> rendah</li>
                    <li><i>Crime rate</i> menengah ke atas</li>
                  </ul>
                </td>\
              </tr>
              
            </table>
          </div>
          '''
        st.markdown(all_table, unsafe_allow_html=True)
      with char_crime :
        crime_table = '''
          <div style="overflow-x:auto;">
            <table>
              <caption style="caption-side: top; text-align: center;"><i>Cluster</i> Indikator Kriminalitas</caption>
              <tr>
                <th>Nomor <i>Cluster</i></th>
                <th>Nama <i>Cluster</i></th>
                <th>Karakteristik</th>
              </tr>
              <tr>
                <td>1 (merah)</td>
                <td><i>High crime</i><br>(Kriminalitas tinggi)</td>
                <td>
                  <ul>
                    <li><i>Crime total</i> tinggi</li>
                    <li><i>Crime rate</i> menengah ke bawah</li>
                  </ul>
                </td>\
              </tr>
              <tr>
                <td>2 (hijau)</td>
                <td><i>Very high crime</i><br>(Kriminalitas sangat tinggi)</td>
                <td>
                  <ul>
                    <li><i>Crime total</i> menengah ke atas</li>
                    <li><i>Crime rate</i> menengah ke atas</li>
                  </ul>
                </td>\
              </tr>
              <tr>
                <td>3 (ungu)</td>
                <td><i>Very low crime</i><br>(Kriminalitas sangat rendah)</td>
                <td>
                  <ul>
                    <li><i>Crime total</i> rendah</li>
                    <li><i>Crime rate</i> rendah</li>
                  </ul>
                </td>\
              </tr>
              <tr>
                <td>4 (biru)</td>
                <td><i>Low crime</i><br>(Kriminalitas rendah)</td>
                <td>
                  <ul>
                    <li><i>Crime total</i> rendah</li>
                    <li><i>Crime rate</i> menengah ke atas</li>
                  </ul>
                </td>\
              </tr>
            </table>
          </div>
          '''
        st.markdown(crime_table, unsafe_allow_html=True)
      st.write("\n")
