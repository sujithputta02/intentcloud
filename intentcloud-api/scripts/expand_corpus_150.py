"""
IntentCloud - 150+ Multi-Format Corpus Generator & Expander (Objective 1)
Generates 150+ mixed-format documents (PDF, DOCX, TXT) across 10 technical domains:
1. Distributed Systems (Kafka, Raft, Paxos, Stream Processing)
2. Software Architecture (Microservices, Event-Driven, Circuit Breakers, CQRS)
3. Machine Learning & Deep Learning (Transformers, Attention, CNNs, Optimization)
4. Information Retrieval & Search (BM25, Dense Embeddings, RRF, Cross-Encoders)
5. Cloud Computing & Kubernetes (Containers, Orchestration, Ingress, Pod Scaling)
6. Edge & IoT Systems (ARM Cortex, Raspberry Pi, Thermal Profiles, MQTT)
7. Database Systems & Storage (LSM Trees, B-Trees, Write-Ahead Logs, Sharding)
8. Cybersecurity & Zero-Trust (TLS, Cryptography, OAuth2, Tunnels)
9. Operating Systems & Concurrency (Virtual Memory, Scheduling, Mutexes, Async)
10. DevOps & SRE (CI/CD, Monitoring, Observability, SLO/SLA)

Supports version lineage: generates v1 and v2 pairs to test Objective 3 recency/lineage.
"""

from pathlib import Path
import os
import io
import zipfile

BASE_DIR = Path(__file__).resolve().parent.parent / "test_corpus" / "corpus_150"

DOMAINS = {
    "distributed_systems": [
        ("kafka_replication_protocols", "Apache Kafka partition replication, in-sync replicas (ISR), high watermark offset, and leader election under network partitions."),
        ("stream_processing_backpressure", "Reactive streams backpressure handling, flow control buffers, windowed aggregations, and dynamic rate limiting."),
        ("raft_consensus_algorithm", "Raft consensus protocol state transitions: leader election, log replication, heartbeat intervals, and commit indexes."),
        ("distributed_transactions_2pc", "Two-Phase Commit (2PC) protocol, coordinator failure states, and Saga orchestration for distributed data consistency."),
        ("vector_clocks_and_causality", "Logical clocks, Lamport timestamps, and vector clocks for partial ordering in decentralized distributed systems."),
    ],
    "software_architecture": [
        ("microservices_circuit_breaker", "Resilience4j and Netflix Hystrix circuit breaker states: closed, open, half-open failure thresholds, and thread pool isolation."),
        ("event_driven_event_sourcing", "Event sourcing architecture with Command Query Responsibility Segregation (CQRS), event stores, and snapshotting for aggregate reconstruction."),
        ("api_gateway_rate_limiting", "Token bucket and leaky bucket rate limiting algorithms implemented in Envoy, Kong, and Spring Cloud API Gateways."),
        ("domain_driven_design_patterns", "Bounded contexts, aggregates, entities, value objects, and domain events in enterprise domain-driven design."),
        ("database_sharding_strategies", "Horizontal database partitioning, consistent hashing rings, virtual nodes, and cross-shard querying trade-offs."),
    ],
    "machine_learning": [
        ("transformer_multihead_attention", "Scaled dot-product attention, query-key-value matrix projections, and multi-head attention mechanics in transformer encoders."),
        ("convolutional_neural_networks", "Convolution kernels, receptive fields, stride, padding, feature map pooling, and residual skip connections in deep CNNs."),
        ("adam_optimizer_mathematics", "First and second moment estimation with bias corrections and weight decay decoupling in Adam and AdamW optimizers."),
        ("quantization_methods_int8", "Post-training quantization (PTQ) and quantization-aware training (QAT) mapping 32-bit floating point weights to INT8 representations."),
        ("loss_functions_and_backprop", "Cross-entropy loss, negative log-likelihood, and backpropagation chain rule gradient updates across neural network layers."),
    ],
    "information_retrieval": [
        ("bm25_probabilistic_formulation", "Okapi BM25 scoring formula: inverse document frequency (IDF) saturation and sub-linear term frequency document length normalization."),
        ("dense_passage_retrieval_biencoder", "Dual-encoder siamese architectures for dense passage retrieval using inner product nearest neighbors and MIPS."),
        ("reciprocal_rank_fusion_mechanics", "Scale-invariant Reciprocal Rank Fusion (RRF, k=60) combining heterogeneous ranking distributions into an integrated candidate pool."),
        ("cross_encoder_reranking_attention", "Full cross-attention token interactions in cross-encoders for precision query-document reranking and classification."),
        ("calibrated_confidence_abstention", "Logistic sigmoid confidence gating on cross-encoder logits for out-of-domain query abstention and hallucination prevention."),
    ],
    "cloud_computing": [
        ("kubernetes_pod_lifecycle", "Kubernetes pod phases, init containers, readiness probes, liveness probes, and graceful termination pre-stop hooks."),
        ("container_runtime_cgroups", "Linux cgroups v2 resource limits, namespaces isolation, and OCI container execution mechanics under containerd."),
        ("serverless_cold_start_mitigation", "Function-as-a-Service cold start latency analysis, provisioned concurrency, pre-warming, and snapshot restore."),
        ("service_mesh_mtls_security", "Istio and Linkerd service mesh data planes with Envoy sidecar proxies and automatic mTLS certificate rotation."),
        ("cloud_cost_optimization_sre", "Spot instance orchestration, auto-scaling horizontal pod autoscalers (HPA), and resource allocation quotas in cloud clusters."),
    ],
    "edge_iot": [
        ("raspberry_pi_thermal_throttling", "Thermal dissipation on ARM Cortex-A72: passive vs active cooling, CPU frequency governor scaling, and DVFS throttling."),
        ("mqtt_protocol_iot_telemetry", "MQTT QoS levels 0, 1, 2, keep-alive pinging, last will and testament, and topic wildcards for constrained edge devices."),
        ("embedded_vector_databases_edge", "Embedded vector storage using Qdrant and SQLite-VSS on memory-constrained single-board edge hardware."),
        ("edge_inference_onnx_runtime", "Optimizing neural inference latency on ARM NEON SIMD instructions using INT8 ONNX Runtime execution providers."),
        ("low_power_energy_characterization", "Measuring Joules-per-query on 15-watt single-board computers under continuous transformer inference loads."),
    ],
    "database_systems": [
        ("lsm_tree_storage_engines", "Log-Structured Merge-tree architecture: in-memory MemTable, Write-Ahead Log (WAL), and multi-level SSTable compaction."),
        ("b_tree_indexing_internals", "B+ Tree node splitting, branch factor, disk page alignment, sibling pointers, and range scan performance."),
        ("acid_isolation_levels", "Read Uncommitted, Read Committed, Repeatable Read, and Serializable snapshot isolation anomalies: dirty reads and phantom reads."),
        ("write_ahead_logging_recovery", "ARIES recovery algorithm: analysis, redo, and undo phases for database crash consistency and checkpointing."),
        ("columnar_storage_parquet", "Column-oriented storage formats, dictionary encoding, run-length encoding (RLE), and bit-packing in Apache Parquet."),
    ],
    "cybersecurity": [
        ("tls_handshake_cryptography", "TLS 1.3 cryptographic handshake: Ephemeral Diffie-Hellman key exchange, AEAD ciphers, and 0-RTT early data risks."),
        ("oauth2_pkce_authorization", "OAuth 2.0 Authorization Code flow with Proof Key for Code Exchange (PKCE) for public and native clients."),
        ("zero_trust_network_tunnels", "Outbound-only reverse tunnels, identity-aware proxies, and Cloudflare Zero-Trust architecture without inbound open ports."),
        ("cross_site_request_forgery", "SameSite cookie policies, anti-CSRF synchronizer tokens, and defense-in-depth web application protection."),
        ("sql_injection_defense_mechanisms", "Parameterized prepared statements, abstract syntax tree (AST) validation, and least-privilege database user roles."),
    ],
    "operating_systems": [
        ("virtual_memory_paging_algorithms", "Hierarchical page tables, Translation Lookaside Buffer (TLB) misses, and Least Recently Used (LRU) page replacement policies."),
        ("process_scheduling_algorithms", "Completely Fair Scheduler (CFS), red-black tree runqueues, nice values, and priority decay in the Linux kernel."),
        ("concurrency_deadlock_detection", "Coffman conditions, resource allocation graphs, and Banker's algorithm for deadlock avoidance in multi-threaded systems."),
        ("async_event_loop_epoll", "Non-blocking I/O multiplexing with epoll edge-triggered notifications, kqueue, and asynchronous event loops."),
        ("memory_allocator_ptmalloc_jemalloc", "Thread local caching, arenas, heap fragmentation mitigation, and slab allocation mechanics in jemalloc."),
    ],
    "devops_sre": [
        ("ci_cd_pipeline_best_practices", "Automated regression testing, semantic versioning, and canary deployment verification in GitHub Actions."),
        ("prometheus_metrics_monitoring", "Counters, gauges, histograms, and summary metric types in Prometheus time-series databases with PromQL alerts."),
        ("distributed_tracing_opentelemetry", "Span context propagation, W3C traceparent headers, and distributed trace sampling with Jaeger and OpenTelemetry."),
        ("error_budgets_and_slo", "Defining Service Level Indicators (SLI), Service Level Objectives (SLO), and error budget burn rate multi-window alerts."),
        ("infrastructure_as_code_terraform", "Declarative state management, resource dependency DAG graphs, and configuration drift detection in Terraform."),
    ],
}


def generate_pdf(file_path: Path, title: str, content: str):
    """Create a formatted PDF document using pure Python standard library."""
    # Format lines
    safe_title = title.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    safe_content = content.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    
    words = safe_content.split()
    body_lines = []
    cur = []
    for w in words:
        cur.append(w)
        if len(" ".join(cur)) > 68:
            body_lines.append(" ".join(cur))
            cur = []
    if cur:
        body_lines.append(" ".join(cur))

    domain_name = file_path.parent.name.replace("_", " ").title()
    doc_id = file_path.stem

    stream_data = f"BT /F1 14 Tf 50 760 Td ({safe_title}) Tj ET\n"
    stream_data += f"BT /F1 10 Tf 50 740 Td (Domain: {domain_name} | Document ID: {doc_id}) Tj ET\n"
    stream_data += f"BT /F1 10 Tf 50 725 Td (Specification Standard: IEEE Capstone Evaluation Corpus) Tj ET\n"
    stream_data += f"BT /F1 11 Tf 50 700 Td (Executive Overview:) Tj ET\n"

    y = 680
    for line in body_lines:
        stream_data += f"BT /F1 10 Tf 50 {y} Td ({line}) Tj ET\n"
        y -= 14

    y -= 15
    stream_data += f"BT /F1 11 Tf 50 {y} Td (Methodological Verification & System Lineage:) Tj ET\n"
    y -= 18
    extra_lines = [
        "This specification is catalogued in IntentCloud for intent-aware hybrid retrieval.",
        "Text chunks are indexed into 384-dimensional dense semantic vectors and",
        "1,000,003-dimensional sparse feature-hashed token projections.",
        "Candidate pools are unified using scale-invariant Reciprocal Rank Fusion (k=60).",
        "Explainable citation attribution is extracted using cross-encoder cross-attention."
    ]
    for line in extra_lines:
        safe_l = line.replace("(", "\\(").replace(")", "\\)")
        stream_data += f"BT /F1 9 Tf 50 {y} Td ({safe_l}) Tj ET\n"
        y -= 13

    stream_bytes = stream_data.encode("latin1", errors="ignore")

    pdf = bytearray()
    pdf.extend(b"%PDF-1.4\n")

    o1 = len(pdf)
    pdf.extend(b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")

    o2 = len(pdf)
    pdf.extend(b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n")

    o3 = len(pdf)
    pdf.extend(b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n")

    o4 = len(pdf)
    pdf.extend(f"4 0 obj\n<< /Length {len(stream_bytes)} >>\nstream\n".encode("latin1"))
    pdf.extend(stream_bytes)
    pdf.extend(b"\nendstream\nendobj\n")

    o5 = len(pdf)
    pdf.extend(b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n")

    xref_pos = len(pdf)
    pdf.extend(b"xref\n0 6\n0000000000 65535 f \n")
    for offset in [o1, o2, o3, o4, o5]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("latin1"))

    pdf.extend(f"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n".encode("latin1"))

    with open(file_path, "wb") as f:
        f.write(pdf)


def generate_docx(file_path: Path, title: str, content: str):
    """Create a formatted DOCX document using pure Python zipfile and XML."""
    content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>"""

    rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""

    safe_title = title.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    safe_content = content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    domain_name = file_path.parent.name.replace("_", " ").title()

    document_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p>
      <w:pPr><w:pStyle w:val="Heading1"/></w:pPr>
      <w:r><w:t>{safe_title}</w:t></w:r>
    </w:p>
    <w:p>
      <w:r><w:b/><w:t>Domain: {domain_name} | Document: {file_path.name}</w:t></w:r>
    </w:p>
    <w:p>
      <w:pPr><w:pStyle w:val="Heading2"/></w:pPr>
      <w:r><w:t>Overview and System Specifications</w:t></w:r>
    </w:p>
    <w:p>
      <w:r><w:t>{safe_content}</w:t></w:r>
    </w:p>
    <w:p>
      <w:pPr><w:pStyle w:val="Heading2"/></w:pPr>
      <w:r><w:t>Technical Architecture and Evaluation Protocol</w:t></w:r>
    </w:p>
    <w:p>
      <w:r><w:t>This specification is catalogued in IntentCloud for intent-aware hybrid retrieval, supporting query-adaptive recency scoring and multi-graded evaluation across IEEE Phase-1 benchmarks.</w:t></w:r>
    </w:p>
    <w:tbl>
      <w:tr>
        <w:tc><w:p><w:r><w:b/><w:t>Parameter</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:b/><w:t>Target Specification</w:t></w:r></w:p></w:tc>
      </w:tr>
      <w:tr>
        <w:tc><w:p><w:r><w:t>Retrieval Mode</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:t>Mode C: Hybrid RRF (k=60) + Cross-Encoder</w:t></w:r></w:p></w:tc>
      </w:tr>
      <w:tr>
        <w:tc><w:p><w:r><w:t>Target Latency</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:t>&lt;= 15.0 s (Edge Constraint)</w:t></w:r></w:p></w:tc>
      </w:tr>
    </w:tbl>
  </w:body>
</w:document>"""

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", content_types)
        z.writestr("_rels/.rels", rels)
        z.writestr("word/document.xml", document_xml)

    with open(file_path, "wb") as f:
        f.write(buf.getvalue())

def generate_txt(file_path: Path, title: str, content: str):
    """Create a plain text document."""
    text = (
        f"# {title.replace('_', ' ').title()}\n\n"
        f"Domain: {file_path.parent.name.replace('_', ' ').title()}\n"
        f"Filename: {file_path.name}\n\n"
        f"## Abstract\n{content}\n\n"
        f"## Implementation Notes\n"
        f"Local-first document indexed into 384-dimensional dense semantic vectors "
        f"and 1,000,003-dimensional sparse token hashes.\n"
    )
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(text)

def build_corpus_150():
    """Build the complete 150+ document corpus across PDF, DOCX, and TXT formats."""
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    count = 0

    for domain_name, topic_list in DOMAINS.items():
        domain_dir = BASE_DIR / domain_name
        domain_dir.mkdir(parents=True, exist_ok=True)
        
        for topic_slug, topic_desc in topic_list:
            # 1. Base PDF version (v1)
            pdf_path_v1 = domain_dir / f"{topic_slug}_v1.pdf"
            generate_pdf(pdf_path_v1, f"{topic_slug} (Initial Draft)", topic_desc)
            count += 1

            # 2. Updated DOCX version (v2 - Lineage pair)
            docx_path_v2 = domain_dir / f"{topic_slug}_v2.docx"
            generate_docx(docx_path_v2, f"{topic_slug} (Revised Specification)", f"Revised edition: {topic_desc} Includes updated benchmarks and latency parameters.")
            count += 1

            # 3. Plain text operational notes (v1 or standalone)
            txt_path = domain_dir / f"{topic_slug}_notes.txt"
            generate_txt(txt_path, f"{topic_slug} Notes", f"Operational engineering notes: {topic_desc}")
            count += 1

    print(f"✓ Successfully generated {count} mixed-format documents in {BASE_DIR}")
    return count

if __name__ == "__main__":
    build_corpus_150()
