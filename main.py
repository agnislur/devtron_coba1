#from flask import Flask

#app = Flask(__name__)

#@app.route('/')
#def hello():
#    return "<strong>Hello World! Versi 4.0 - Diperbarui secara otomatis oleh Devtron!</strong> coba homing" 

#if __name__ == '__main__':
    # Listen on all network interfaces, so it's accessible within the cluster
#    app.run(host='0.0.0.0', port=5000)


import functions_framework
import firebase_admin
from firebase_admin import firestore
import uuid
import requests
import os

# Inisialisasi Firestore jika belum ada
if not firebase_admin._apps:
    firebase_admin.initialize_app()

db = firestore.client()

# Ganti dengan URL DMS-POC Anda yang sebenarnya
DMS_FUNCTION_URL = "https://dms-poc-345665819895.asia-east1.run.app"

@functions_framework.http
def create_vnf_instance(request):
    """
    Fungsi ini sekarang menerima request dengan 'requirements' 
    dan menjalankan logika homing sebelum membuat instance.
    """
    
    ## 1. Menerima request homing dari Devtron
    request_json = request.get_json(silent=True)
    if not request_json or 'requirements' not in request_json:
        print("Error: Request tidak valid, 'requirements' tidak ditemukan.")
        return {"status": "error", "message": "Request JSON tidak valid atau tidak mengandung 'requirements'"}, 400

    vnf_name = request_json.get('vnf_name', 'unknown_vnf')
    vnf_reqs = request_json.get('requirements', {})
    
    print(f"Tacker: Menerima request homing untuk {vnf_name} dengan kebutuhan: {vnf_reqs}")

    ## 2. Mengambil inventaris cloud dari Firestore
    try:
        print("Tacker: Mengambil inventaris cloud dari Firestore...")
        all_clusters_stream = db.collection('cloud_inventory').stream()
        all_clusters = [doc.to_dict() for doc in all_clusters_stream]
        if not all_clusters:
            raise ValueError("Inventaris cloud kosong atau tidak ditemukan.")
    except Exception as e:
        print(f"Error saat mengambil inventaris: {e}")
        return {"status": "error", "message": "Gagal mengambil inventaris cloud"}, 500

    ## 3. Menjalankan logika homing (matchmaking)
    print("Tacker: Memulai proses homing...")
    selected_cluster = None
    for cluster_data in all_clusters:
        # Cek apakah sumber daya mencukupi
        cpu_ok = cluster_data.get('available_cpu', 0) >= vnf_reqs.get('required_cpu', 0)
        ram_ok = cluster_data.get('available_ram_gb', 0) >= vnf_reqs.get('required_ram_gb', 0)
        
        # Cek apakah semua fitur yang dibutuhkan ada di cluster
        required_features = set(vnf_reqs.get('required_features', []))
        available_features = set(cluster_data.get('special_features', []))
        features_ok = required_features.issubset(available_features)
        
        if cpu_ok and ram_ok and features_ok:
            print(f"Tacker: Menemukan cluster yang cocok: {cluster_data.get('cluster_id')}")
            selected_cluster = cluster_data
            break # Hentikan loop jika sudah menemukan yang cocok

    if not selected_cluster:
        print("Tacker: Homing GAGAL. Tidak ada cluster yang cocok.")
        return {"status": "error", "message": "Homing failed: No suitable cluster found"}, 400

    target_cluster_id = selected_cluster.get('cluster_id')
    print(f"Tacker: Homing BERHASIL. Cluster terpilih: {target_cluster_id}")

    ## 4. Memanggil API DMS untuk membuat placeholder
    try:
        print(f"Tacker: Memanggil API DMS di {DMS_FUNCTION_URL}")
        dms_response = requests.post(DMS_FUNCTION_URL, json={'vnf_name': vnf_name})
        dms_response.raise_for_status()
        dms_data = dms_response.json()
        placeholder_id = dms_data.get('placeholder_id')
        if not placeholder_id:
            raise ValueError("Respon dari DMS tidak valid, tidak ada 'placeholder_id'.")
        print(f"Tacker: DMS mengonfirmasi pembuatan placeholder: {placeholder_id}")

    except requests.exceptions.RequestException as e:
        print(f"Error: Gagal memanggil DMS. {e}")
        return {"status": "error", "message": "Gagal berkomunikasi dengan DMS"}, 500

    ## 5. Membuat entri VNF Instance di Firestore DENGAN HASIL HOMING
    vnf_instance_id = f"vnf-{uuid.uuid4()}"
    doc_ref = db.collection('vnfm_instances').document(vnf_instance_id)
    doc_ref.set({
        'product_name': vnf_name,
        'instantiation_state': 'NOT_INSTANTIATED',
        'dms_placeholder_id': placeholder_id,
        'target_cluster_id': target_cluster_id, # <-- HASIL HOMING DISIMPAN DI SINI
        'timestamp': firestore.SERVER_TIMESTAMP
    })

    ## 6. Mengirim balasan sukses ke SMO/Devtron
    print(f"Tacker: Mengirim balasan ke SMO dengan VNF Instance ID: {vnf_instance_id}")
    return {
        'vnfInstanceId': vnf_instance_id, 
        'state': 'NOT_INSTANTIATED',
        'homing_decision': {
            'target_cluster_id': target_cluster_id
        }
    }, 201
