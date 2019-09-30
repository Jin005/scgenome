###############
# Do BHC, Naive and UMAP/HDBSCAN clustering on a dataset
import pandas as pd
import numpy as np
from scgenome import cncluster, utils, simulation, cnplot
import scipy.cluster.hierarchy as sch
import os
import time
import matplotlib.pyplot as plt
import sklearn.metrics as skm

from scgenome.constants import LOG_P5

OUT_DIR = "/Users/massoudmaher/data/test_do_clustering/"
CN_DATA_FP = "/Users/massoudmaher/data/clean_sc_1935_1936_1937_cn_data_qc.csv"
SEED = None

N_CELLS = 100  # Set to None if we want all cells
N_BIN = 100

# BHC Params
N_STATES = 12
ALPHA = 10
PROB_CN_SAME = 0.8

# Naive params
NAIVE_METHOD = 'single'
NAIVE_METRIC = 'euclidean'

# UMAP / HDBSCAN params
UMAP_NN = 5
UMAP_MIN_DIST = 0.1

# Spike in params (not always used)
SAMPLE_IDS = ['SC-1935', 'SC-1936', 'SC-1937']
spike_in = True
PROPORTIONS = None  # Set to None for equal proportion of each sample

if not os.path.exists(OUT_DIR):
    print(f"{OUT_DIR} does not exist, creating it")
    os.makedirs(OUT_DIR)

print(f"Reading in {CN_DATA_FP}")
cn_data = pd.read_csv(CN_DATA_FP)

if N_CELLS is not None:
    if spike_in:
        cn_data = utils.get_cn_data_submixture(cn_data, N_CELLS, SAMPLE_IDS,
                                               proportions=PROPORTIONS)
    else:
        cells = pd.Series(np.unique(cn_data["cell_id"]))
        keep_cells = cells.sample(N_CELLS, random_state=SEED)
        cn_data = cn_data[cn_data["cell_id"].isin(keep_cells)]

if N_BIN is not None:
    end_val = np.unique(cn_data["end"])[N_BIN]
    print(f"Reducing to {N_BIN} bins, end: {end_val}")
    cn_data = cn_data[cn_data["end"] <= end_val]

if N_CELLS is not None or N_BIN is not None:
    cn_data.to_csv(os.path.join(OUT_DIR, "cn_data.csv"))

n_cell = np.unique(cn_data["cell_id"]).shape[0]
n_bin = np.unique(cn_data["end"]).shape[0]

print(f"cn_data.shape {cn_data.shape}")

print(f"Doing UM+HDB on {n_cell} cells, {n_bin} bins")
start = time.time()
cn = (cn_data.set_index(['chr', 'start', 'end', 'cell_id'])['copy']
        .unstack(level='cell_id').fillna(0))
uh_cluster = cncluster.umap_hdbscan_cluster(cn, n_components=2,
                                            n_neighbors=UMAP_NN,
                                            min_dist=UMAP_MIN_DIST)
print(f"{time.time()-start}s for UM+HDB on {n_cell} cells, {n_bin} bins\n\n")
uh_cluster.columns = ['cell_id', 'umap_cluster_id', 'umap1', 'umap2']
print(set(uh_cluster['umap_cluster_id']))

print("Plotting")
# UMAP+HDBSCAN
cn_data = cn_data.merge(uh_cluster)
print(f"cn_data.shape {cn_data.shape}")
# Scatterplot
fig = plt.figure(figsize=(8, 8))
nuh_cluster = uh_cluster.copy()
nuh_cluster.columns = ['cell_id', 'cluster_id', 'umap1', 'umap2']
cncluster.plot_umap_clusters(plt.gca(), nuh_cluster)
fig.savefig(os.path.join(OUT_DIR, "uh_scatter.png"), bbox_inches='tight')
# Heatmap
fig = plt.figure(figsize=(10, 8))
bimatrix_data, ps = cnplot.plot_clustered_cell_cn_matrix_figure(
    fig, cn_data, "copy", cluster_field_name="umap_cluster_id",
    linkage=None, origin_field_name=None,
    raw=True,
    flip=False)
fig.savefig(os.path.join(OUT_DIR, "umap_heatmap.png"), bbox_inches='tight')

# TODO make it so you can plot when there is no origin
