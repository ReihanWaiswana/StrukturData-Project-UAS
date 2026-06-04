import streamlit as st
import pandas as pd
import folium
import openrouteservice

API_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjE0YzM1Y2QxNzlkMTQwMjc5NTVkMDQwMGI1ZDA5YzU3IiwiaCI6Im11cm11cjY0In0="

client = openrouteservice.Client(key=API_KEY)

from streamlit_folium import st_folium

from graph.graph_builder import build_graph
from algorithms.dijkstra import dijkstra
from folium.plugins import HeatMap
import networkx as nx
import matplotlib.pyplot as plt


# =====================================
# CONFIG
# =====================================

st.set_page_config(
    page_title="DSS Evakuasi Bencana",
    layout="wide"
)

# =====================================
# SIDEBAR
# =====================================

st.sidebar.title("Menu DSS")

jenis_bencana = st.sidebar.selectbox(
    "Jenis Bencana",
    [
        "Gempa",
        "Banjir",
        "Tsunami"
    ]
)

# =====================================
# LOAD DATA
# =====================================

nodes_df = pd.read_csv("dataset/nodes.csv")
edges_df = pd.read_csv("dataset/edges.csv")

hindari_bahaya = st.sidebar.checkbox(
    "Hindari Area Berbahaya",
    value=True
)

graph = build_graph(
    "dataset/edges.csv",
    jenis_bencana,
    avoid_danger=hindari_bahaya
)

lokasi_awal = st.sidebar.selectbox(
    "Lokasi Awal",
    nodes_df['id']
)

tujuan = st.sidebar.selectbox(
    "Tujuan Evakuasi",
    nodes_df['id']
)


# =====================================
# TAMBAH LOKASI
# =====================================

st.sidebar.subheader("Tambah Titik Lokasi")

# =====================================
# TAMBAH JALUR / EDGE
# =====================================

st.sidebar.subheader("Tambah Jalur")

edge_source = st.sidebar.selectbox(
    "Dari Lokasi",
    nodes_df['id'],
    key="edge_source"
)

edge_target = st.sidebar.selectbox(
    "Ke Lokasi",
    nodes_df['id'],
    key="edge_target"
)

edge_weight = st.sidebar.number_input(
    "Bobot / Jarak",
    min_value=1,
    value=1
)

edge_status = st.sidebar.selectbox(
    "Status Jalur",
    ["Aman", "Bahaya"]
)

if st.sidebar.button("Tambah Jalur"):

    new_edge = {
        'source': edge_source,
        'target': edge_target,
        'weight': edge_weight,
        'status': edge_status
    }

    edges_df = pd.concat(
        [edges_df, pd.DataFrame([new_edge])],
        ignore_index=True
    )

    edges_df.to_csv(
        "dataset/edges.csv",
        index=False
    )

    st.sidebar.success("Jalur berhasil ditambahkan")

new_id = st.sidebar.text_input("ID Lokasi")

new_nama = st.sidebar.text_input("Nama Lokasi")

new_tipe = st.sidebar.selectbox(
    "Tipe Lokasi",
    ["Aman", "Bahaya", "Bangunan", "Medis"]
)

new_lat = st.sidebar.number_input(
    "Latitude",
    format="%.6f"
)

new_lon = st.sidebar.number_input(
    "Longitude",
    format="%.6f"
)

if st.sidebar.button("Tambah Lokasi"):

    new_data = {
        'id': new_id,
        'lokasi': new_nama,
        'tipe': new_tipe,
        'lat': new_lat,
        'lon': new_lon
    }

    nodes_df = pd.concat(
        [nodes_df, pd.DataFrame([new_data])],
        ignore_index=True
    )

    nodes_df.to_csv(
        "dataset/nodes.csv",
        index=False
    )

    st.sidebar.success("Lokasi berhasil ditambahkan")

# =====================================
# HEADER
# =====================================

st.title("DSS Jalur Evakuasi Bencana")

st.markdown(
    "Sistem rekomendasi jalur evakuasi berbasis graph menggunakan algoritma Dijkstra"
)

# =====================================
# STATISTIK
# =====================================

col1, col2 = st.columns(2)

with col1:
    st.metric(
        "Jumlah Lokasi",
        len(nodes_df)
    )

with col2:
    st.metric(
        "Jumlah Jalur",
        len(edges_df)
    )

danger_count = len(
    nodes_df[nodes_df['tipe'] == 'Bahaya']
)

safe_route = len(
    edges_df[edges_df['status'] == 'Aman']
)

col3, col4 = st.columns(2)

with col3:
    st.metric(
        "Zona Bahaya",
        danger_count
    )

with col4:
    st.metric(
        "Jalur Aman",
        safe_route
    )

# =====================================
# PROSES DIJKSTRA
# =====================================

def path_has_danger(path, edges):
    for i in range(len(path) - 1):
        source = path[i]
        target = path[i + 1]
        row = edges[
            (edges['source'] == source)
            & (edges['target'] == target)
        ]
        if not row.empty and row.iloc[0]['status'] == 'Bahaya':
            return True
    return False

if 'best_path' not in st.session_state:
    st.session_state.best_path = []

if 'total_cost' not in st.session_state:
    st.session_state.total_cost = 0

if st.sidebar.button("Cari Jalur Terbaik"):
    result = dijkstra(
        graph,
        lokasi_awal,
        tujuan
    )

    # dijkstra sekarang mengembalikan (cost, path, steps)
    if len(result) == 3:
        total_cost, best_path, steps = result
    else:
        total_cost, best_path = result
        steps = []

    st.session_state.best_path = best_path
    st.session_state.total_cost = total_cost
    st.session_state.dijkstra_steps = steps

    if not st.session_state.best_path:
        st.error("Jalur tidak ditemukan")

# =====================================
# PETA
# =====================================

center_lat = nodes_df['lat'].mean()
center_lon = nodes_df['lon'].mean()

m = folium.Map(
    location=[center_lat, center_lon],
    zoom_start=15,
    tiles="CartoDB positron"
)

from folium.plugins import MiniMap
from folium.plugins import Fullscreen

MiniMap().add_to(m)
Fullscreen().add_to(m)

# =====================================
# MARKER
# =====================================

heat_data = []

for _, row in nodes_df.iterrows():
    color = "blue"

    if row['tipe'] == "Bahaya":
        color = "red"
    elif row['tipe'] == "Aman":
        color = "green"
    elif row['tipe'] == "Medis":
        color = "orange"

    folium.Marker(
        location=[row['lat'], row['lon']],
        popup=row['lokasi'],
        icon=folium.Icon(color=color)
    ).add_to(m)

    if row['tipe'] == "Bahaya":
        heat_data.append([
            row['lat'],
            row['lon'],
            1
        ])

if heat_data:
    HeatMap(
        heat_data,
        radius=40,
        blur=25
    ).add_to(m)

# =====================================
# ROUTE MENGIKUTI JALAN ASLI
# =====================================

if (
    st.session_state.best_path
    and len(st.session_state.best_path) > 1
):

    coordinates = []

    for node in st.session_state.best_path:

        row = nodes_df[
            nodes_df['id'] == node
        ].iloc[0]

        coordinates.append((
            row['lon'],
            row['lat']
        ))

    try:

        route = client.directions(
            coordinates=coordinates,
            profile='driving-car',
            format='geojson'
        )

        route_coords = route['features'][0][
            'geometry'
        ]['coordinates']

        real_route = [
            [coord[1], coord[0]]
            for coord in route_coords
        ]

        folium.PolyLine(
            real_route,
            color='blue',
            weight=8,
            opacity=1,
            tooltip='Rute Evakuasi'
        ).add_to(m)

        folium.Marker(
            location=real_route[0],
            popup="Lokasi Awal",
            icon=folium.Icon(color="green")
        ).add_to(m)

        folium.Marker(
            location=real_route[-1],
            popup="Tujuan Evakuasi",
            icon=folium.Icon(color="red")
        ).add_to(m)

    except Exception as e:

        st.error(f"Routing error: {e}")

# =====================================
# TAMPILKAN MAP
# =====================================

st.subheader("Peta Evakuasi")

st_folium(
    m,
    width=1200,
    height=600
)

# =====================================
# TAMPILAN DATA INPUT
# =====================================

st.subheader("Data Input: Nodes dan Edges")
with st.expander("Tabel Nodes"):
    st.dataframe(nodes_df)

with st.expander("Tabel Edges"):
    st.dataframe(edges_df)

# =====================================
# VISUALISASI GRAPH (NETWORKX)
# =====================================

st.subheader("Visualisasi Graph (Network)")
G = nx.DiGraph()

for _, row in nodes_df.iterrows():
    G.add_node(row['id'], label=row['lokasi'], pos=(row['lon'], row['lat']), tipe=row['tipe'])

for _, row in edges_df.iterrows():
    G.add_edge(row['source'], row['target'], weight=row['weight'], status=row['status'])

pos = {n: (data['pos'][0], data['pos'][1]) for n, data in G.nodes(data=True)}

fig, ax = plt.subplots(figsize=(8, 6))
node_colors = []
for _, data in G.nodes(data=True):
    if data.get('tipe') == 'Bahaya':
        node_colors.append('red')
    elif data.get('tipe') == 'Aman':
        node_colors.append('green')
    elif data.get('tipe') == 'Medis':
        node_colors.append('orange')
    else:
        node_colors.append('blue')

nx.draw_networkx_nodes(G, pos=pos, node_color=node_colors, node_size=100, ax=ax)
nx.draw_networkx_edges(G, pos=pos, arrows=True, ax=ax)
nx.draw_networkx_labels(G, pos=pos, labels={n: n for n in G.nodes()}, font_size=8, ax=ax)
ax.set_axis_off()
st.pyplot(fig)

# =====================================
# PROSES ANALISIS KEPUTUSAN (LANGKAH)
# =====================================

st.subheader("Proses Analisis Keputusan")
if 'dijkstra_steps' not in st.session_state:
    st.session_state.dijkstra_steps = []

if st.session_state.best_path:
    st.success("Rekomendasi tersedia")
    st.markdown("**Hasil Jalur**")
    st.write(" → ".join(st.session_state.best_path))
    st.markdown("**Total Bobot**")
    st.write(st.session_state.total_cost)

    if path_has_danger(st.session_state.best_path, edges_df):
        if hindari_bahaya:
            st.warning(
                "⚠️ Rute ini masih mengandung area berbahaya karena tidak ada jalur aman lain yang tersedia."
            )
        else:
            st.warning(
                "⚠️ Sistem mendeteksi area berbahaya pada jalur evakuasi"
            )

    steps = st.session_state.dijkstra_steps

    if steps:
        step_idx = st.slider("Pilih Langkah", 1, len(steps), 1)
        snapshot = steps[step_idx - 1]

        with st.expander(f"Snapshot Langkah {step_idx}"):
            st.write(snapshot)

        with st.expander("Semua Langkah"):
            for i, s in enumerate(steps, start=1):
                st.write(f"Langkah {i}")
                st.write(s)
                st.write("---")
else:
    st.info("Tekan tombol 'Cari Jalur Terbaik' di sidebar untuk memulai analisis.")