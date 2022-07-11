#run apps in terminal : streamlit run CriMap.py
#stop apps : ctrl + c
import page.Home as Home
import page.Cluster as Cluster
import page.Map as Map

import streamlit as st
from streamlit_option_menu import option_menu

# Config
st.set_page_config(page_title="CriMap - Criminality Map", page_icon='img/crimap-icon.png', layout="wide", menu_items=None)

# CSS Style
css = '''
<style>
    footer {
        visibility: hidden;
    }

    .block-container {
        padding-top: 2rem;
        align-items: center;
    }

    [title~="st.iframe"] { 
        width: 100%
    }

    .streamlit-expander{
        border: 2pt solid gray;
        border-radius: 5px;
    }

    .streamlit-expanderHeader {
        font-size: x-large;
        color: #3E3636;
    }

    .bg-div {
        border: 2pt solid grey;
        border-radius: 10px;    
        margin-bottom: 30px;
        padding: 50px 80px 50px 80px;
        background-color: #3E3636;
    }
    .bg-div h2, .bg-div p{
        color: #F5EDED;
        text-align: center;
    }

    .gif {
        max-width: 100%;
        max-height: 100%;
        border: 2pt solid gray;
    }

    p {
        text-align: justify;
        color:#3E3636;
    }

    div.row-widget.stRadio > div {
        flex-direction:row;
    }

</style>
'''
st.markdown('<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-EVSTQN3/azprG1Anm3QDgpJLIm9Nao0Yz1ztcQTwFspd3yD65VohhpuuCOmLASjC" crossorigin="anonymous">', unsafe_allow_html=True)
st.markdown(css, unsafe_allow_html=True)

# NavBar
selected = option_menu(
    menu_title = None,
    options = ["Beranda","Peta","Clustering",],
    icons = ["house-fill","map-fill","diagram-3-fill",], #"tools"
    orientation = "horizontal",
    styles={
        "container": {"padding": "0.1!important", "background-color":"#3E3636"},
        "icon": {"font-size": "15px", "margin":"auto", "color":"#F5EDED"}, 
        "nav-link": {"font-size": "15px", "text-align": "center", "color":"#F5EDED", "font-family":"Sans-serif"},
        "nav-link-selected": {"font-weight":"normal", "background-color":"#D72323", "color":"#F5EDED", "font-family":"Sans-serif","margin":"3px"},
    }
)

if selected == "Beranda":
    Home.main()
elif selected == "Peta":
    Map.main()
elif selected == "Clustering":
    Cluster.main()
