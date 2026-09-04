import { useEffect, useMemo, useState } from "react";
import { Navigate } from "react-router-dom";
import DashboardLayout from "../components/layout/DashboardLayout";
import Button from "../components/common/Button";
import { useAuth } from "../hooks/useAuth";
import { fsmAdminAPI } from "../services/api";
import PersibLogo from "../image/Logo_Persib_Bandung.png";
import {
  Layers,
  Menu,
  Terminal,
  ArrowRightLeft,
  Search,
  Plus,
  RotateCw,
  Trash2,
  Save,
  CheckCircle2,
  AlertCircle,
  AlertTriangle,
  Info,
  Code,
  Filter,
  X,
  FileText,
  Sliders,
  ChevronRight,
  Sparkles,
  Link2
} from "lucide-react";
import "../styles/fsm-admin.css";

const NODE_TYPES = [
  { value: "menu_state", label: "Menu State", description: "Menampilkan opsi pilihan menu ke user" },
  { value: "terminal_state", label: "Terminal State", description: "Menampilkan jawaban akhir / mengeksekusi aksi" },
  { value: "transitional_state", label: "Transitional State", description: "Menerima input parameter bebas dari user" },
];

// Semua action handler yang tersedia di core/dispatcher.py
const DISPATCHER_ACTIONS = [
  { value: "static", label: "static", description: "Pesan teks statis (isi langsung di field Content)" },
  { value: "get_jadwal_terdekat", label: "get_jadwal_terdekat", description: "Ambil jadwal pertandingan Persib terdekat" },
  { value: "get_jadwal_pertandingan", label: "get_jadwal_pertandingan", description: "Ambil semua jadwal pertandingan" },
  { value: "get_jadwal_mendatang", label: "get_jadwal_mendatang", description: "Ambil jadwal pertandingan mendatang" },
  { value: "get_jadwal_selesai", label: "get_jadwal_selesai", description: "Ambil jadwal pertandingan yang sudah selesai" },
  { value: "get_jadwal_by_lawan", label: "get_jadwal_by_lawan", description: "Cari jadwal berdasarkan nama klub lawan" },
  { value: "get_stok_tiket_terdekat", label: "get_stok_tiket_terdekat", description: "Cek stok & info tiket pertandingan terdekat" },
  { value: "get_harga_tiket_by_tribun", label: "get_harga_tiket_by_tribun", description: "Ambil harga tiket berdasarkan tribun" },
  { value: "get_harga_tiket", label: "get_harga_tiket", description: "Ambil daftar harga semua tribun tiket" },
  { value: "get_stok_tiket_by_lawan", label: "get_stok_tiket_by_lawan", description: "Cek stok tiket berdasarkan nama lawan" },
  { value: "get_produk_by_kategori", label: "get_produk_by_kategori", description: "Ambil produk merchandise berdasarkan kategori" },
  { value: "get_produk_by_nama", label: "get_produk_by_nama", description: "Cari produk merchandise berdasarkan nama" },
  { value: "get_pemain_by_nama", label: "get_pemain_by_nama", description: "Cari info pemain Persib berdasarkan nama" },
  { value: "get_pemain_by_posisi", label: "get_pemain_by_posisi", description: "Cari pemain berdasarkan posisi bermain" },
  { value: "get_pemain_by_status", label: "get_pemain_by_status", description: "Cari pemain berdasarkan status (aktif/cedera)" },
];

const DEFAULT_ACTION = "static";
const DEFAULT_BACK_TO = "user_menu_utama";

// Komponen SearchableSelect: dropdown dengan fitur search/filter
function SearchableSelect({ value, onChange, options, placeholder = "-- Pilih atau ketik untuk cari --", emptyLabel = "-- Pilih --" }) {
  const [query, setQuery] = useState("");
  const [isOpen, setIsOpen] = useState(false);

  const getOptionValue = (option) => typeof option === "string" ? option : option.value;
  const getOptionLabel = (option) => typeof option === "string" ? option : option.label;

  const filtered = options.filter((opt) =>
    `${getOptionLabel(opt)} ${getOptionValue(opt)}`.toLowerCase().includes(query.toLowerCase())
  );

  const selectedOption = options.find((option) => getOptionValue(option) === value);
  const displayValue = selectedOption ? getOptionLabel(selectedOption) : value || "";

  const handleSelect = (val) => {
    onChange(val);
    setQuery("");
    setIsOpen(false);
  };

  const handleBlur = (e) => {
    if (!e.currentTarget.contains(e.relatedTarget)) {
      setIsOpen(false);
      setQuery("");
    }
  };

  return (
    <div className="ss-wrapper" onBlur={handleBlur} tabIndex={-1}>
      <div
        className={`ss-trigger ${isOpen ? "open" : ""}`}
        onClick={() => setIsOpen((prev) => !prev)}
      >
        <span className={`ss-trigger-text ${!displayValue ? "placeholder" : ""}`}>
          {displayValue || emptyLabel}
        </span>
        <span className="ss-chevron">{isOpen ? "▲" : "▼"}</span>
      </div>
      {isOpen && (
        <div className="ss-dropdown">
          <div className="ss-search-row">
            <input
              className="ss-search-input"
              type="text"
              placeholder="Ketik untuk mencari..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              autoFocus
            />
          </div>
          <ul className="ss-list">
            <li
              className={`ss-option ${displayValue === "" ? "selected" : ""}`}
              onMouseDown={() => handleSelect("")}
            >
              {emptyLabel}
            </li>
            {filtered.length > 0 ? (
              filtered.map((opt) => (
                <li
                  key={getOptionValue(opt)}
                  className={`ss-option ${value === getOptionValue(opt) ? "selected" : ""}`}
                  onMouseDown={() => handleSelect(getOptionValue(opt))}
                >
                  {getOptionLabel(opt)}
                </li>
              ))
            ) : (
              <li className="ss-option ss-no-result">Tidak ada hasil</li>
            )}
          </ul>
        </div>
      )}
    </div>
  );
}

function createEmptyNode() {
  return {
    id: "",
    type: "menu_state",
    message: "",
    action: DEFAULT_ACTION,
    content: "",
    param_key: "",
    back_to: DEFAULT_BACK_TO,
    paramsText: "{}",
    optionsRows: [{ choice: "1", target: "" }],
  };
}

function cloneOptionsRows(options) {
  const rows = Object.entries(options || {}).map(([choice, target]) => ({ choice, target }));
  return rows.length ? rows : [{ choice: "1", target: "" }];
}

function stringifyParams(params) {
  if (!params || Object.keys(params).length === 0) {
    return "{}";
  }
  return JSON.stringify(params, null, 2);
}

function toNullableText(value) {
  const trimmed = value?.trim();
  return trimmed ? trimmed : null;
}

function buildPayload(form) {
  const payload = {
    id: form.id.trim(),
    type: form.type,
    message: toNullableText(form.message),
    action: toNullableText(form.action),
    content: toNullableText(form.content),
    param_key: toNullableText(form.param_key),
    back_to: toNullableText(form.back_to),
  };

  if (form.type === "menu_state") {
    payload.options = form.optionsRows.reduce((acc, row) => {
      const choice = row.choice.trim();
      const target = row.target.trim();
      if (choice && target) {
        acc[choice] = target;
      }
      return acc;
    }, {});
  }

  const paramsText = form.paramsText.trim();
  if (paramsText) {
    payload.params = JSON.parse(paramsText);
  }

  return payload;
}

function formatNodeType(type) {
  return NODE_TYPES.find((item) => item.value === type)?.label || type;
}

function FsmAdmin() {
  const { user } = useAuth();
  const isAdmin = user?.role === "admin" || user?.email?.includes("admin");

  const [nodes, setNodes] = useState([]);
  const [selectedNodeId, setSelectedNodeId] = useState(null);
  const [form, setForm] = useState(createEmptyNode());
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isReloading, setIsReloading] = useState(false);
  const [status, setStatus] = useState({ type: "info", message: "" });

  // Interactive UI state additions
  const [searchQuery, setSearchQuery] = useState("");
  const [typeFilter, setTypeFilter] = useState("all");
  const [activeMobileTab, setActiveMobileTab] = useState("editor"); // 'nodes' | 'editor'
  const [jsonError, setJsonError] = useState("");

  const selectedNode = useMemo(
    () => nodes.find((node) => node.id === selectedNodeId) || null,
    [nodes, selectedNodeId]
  );

  const selectedNodeIds = useMemo(() => nodes.map((node) => node.id), [nodes]);

  // Counts
  const menuCount = useMemo(() => nodes.filter((node) => node.type === "menu_state").length, [nodes]);
  const terminalCount = useMemo(() => nodes.filter((node) => node.type === "terminal_state").length, [nodes]);
  const transitionalCount = useMemo(() => nodes.filter((node) => node.type === "transitional_state").length, [nodes]);

  // Filtered nodes
  const filteredNodes = useMemo(() => {
    return nodes.filter((node) => {
      const matchesType = typeFilter === "all" || node.type === typeFilter;
      const q = searchQuery.toLowerCase().trim();
      if (!q) return matchesType;

      const matchesId = node.id.toLowerCase().includes(q);
      const matchesMsg = (node.message || "").toLowerCase().includes(q);
      const matchesContent = (node.content || "").toLowerCase().includes(q);
      const matchesAction = (node.action || "").toLowerCase().includes(q);

      return matchesType && (matchesId || matchesMsg || matchesContent || matchesAction);
    });
  }, [nodes, typeFilter, searchQuery]);

  const loadNodes = async (preserveSelection = true) => {
    setIsLoading(true);
    setStatus({ type: "info", message: "Memuat data state FSM..." });

    try {
      const response = await fsmAdminAPI.listNodes();
      const nextNodes = response.nodes || [];
      setNodes(nextNodes);

      if (!nextNodes.length) {
        setSelectedNodeId("__new__");
        setForm(createEmptyNode());
        setStatus({ type: "warning", message: "Belum ada node FSM yang terdaftar." });
        return;
      }

      const fallbackId = nextNodes[0].id;
      const nextSelectedId = preserveSelection && nextNodes.some((node) => node.id === selectedNodeId)
        ? selectedNodeId
        : fallbackId;

      setSelectedNodeId(nextSelectedId);
      setStatus({ type: "success", message: `Berhasil memuat ${nextNodes.length} state FSM.` });
    } catch (error) {
      console.error("Gagal memuat node FSM:", error);
      setStatus({ type: "error", message: error.message || "Gagal memuat state FSM." });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadNodes(false);
  }, []);

  useEffect(() => {
    if (selectedNode) {
      setForm({
        id: selectedNode.id || "",
        type: selectedNode.type || "menu_state",
        message: selectedNode.message || "",
        action: selectedNode.action || DEFAULT_ACTION,
        content: selectedNode.content || "",
        param_key: selectedNode.param_key || "",
        back_to: selectedNode.back_to || DEFAULT_BACK_TO,
        paramsText: stringifyParams(selectedNode.params),
        optionsRows: cloneOptionsRows(selectedNode.options),
      });
      setJsonError("");
      return;
    }

    if (selectedNodeId === "__new__") {
      setForm(createEmptyNode());
      setJsonError("");
    }
  }, [selectedNode, selectedNodeId]);

  if (!isAdmin) {
    return <Navigate to="/chat" replace />;
  }

  const handleSelectNode = (nodeId) => {
    setSelectedNodeId(nodeId);
    if (window.innerWidth < 1280) {
      setActiveMobileTab("editor");
    }
  };

  const handleNewNode = () => {
    setSelectedNodeId("__new__");
    setForm(createEmptyNode());
    setJsonError("");
    setStatus({ type: "info", message: "Mode State Baru aktif. Silakan isi form di bawah." });
    if (window.innerWidth < 1280) {
      setActiveMobileTab("editor");
    }
  };

  const handleFormChange = (field, value) => {
    setForm((prev) => ({
      ...prev,
      [field]: value,
    }));

    if (field === "paramsText") {
      try {
        if (value.trim()) {
          JSON.parse(value);
        }
        setJsonError("");
      } catch (err) {
        setJsonError(err.message);
      }
    }
  };

  const updateOptionRow = (index, field, value) => {
    setForm((prev) => {
      const nextRows = prev.optionsRows.map((row, rowIndex) => {
        if (rowIndex !== index) return row;
        return { ...row, [field]: value };
      });
      return { ...prev, optionsRows: nextRows };
    });
  };

  const addOptionRow = () => {
    setForm((prev) => ({
      ...prev,
      optionsRows: [...prev.optionsRows, { choice: (prev.optionsRows.length + 1).toString(), target: "" }],
    }));
  };

  const removeOptionRow = (index) => {
    setForm((prev) => {
      const nextRows = prev.optionsRows.filter((_, rowIndex) => rowIndex !== index);
      return {
        ...prev,
        optionsRows: nextRows.length ? nextRows : [{ choice: "1", target: "" }],
      };
    });
  };

  const validateForm = () => {
    if (!form.id.trim()) {
      throw new Error("ID State wajib diisi.");
    }

    if (form.type === "menu_state") {
      if (!form.message.trim()) {
        throw new Error("Menu state wajib memiliki Pesan (Message).");
      }
      const validOptions = form.optionsRows.filter((row) => row.choice.trim() && row.target.trim());
      if (!validOptions.length) {
        throw new Error("Menu state wajib memiliki minimal satu opsi yang valid (Pilihan & Target).");
      }
    }

    if (form.type === "terminal_state") {
      if (!form.action.trim()) {
        throw new Error("Terminal state wajib memiliki Action.");
      }
      if (!form.back_to.trim()) {
        throw new Error("Terminal state wajib memiliki Back To target.");
      }
      if (form.action.trim() === "static" && !form.content.trim()) {
        throw new Error("Action static wajib memiliki Content (isi jawaban).");
      }
    }

    if (form.type === "transitional_state") {
      if (!form.message.trim()) {
        throw new Error("Transitional state wajib memiliki Pesan (Message).");
      }
      if (!form.action.trim()) {
        throw new Error("Transitional state wajib memiliki Action.");
      }
      if (!form.param_key.trim()) {
        throw new Error("Transitional state wajib memiliki Param Key.");
      }
      if (!form.back_to.trim()) {
        throw new Error("Transitional state wajib memiliki Back To target.");
      }
    }

    if (form.paramsText.trim()) {
      JSON.parse(form.paramsText);
    }
  };

  const handleSave = async () => {
    setStatus({ type: "info", message: "Menyimpan perubahan state..." });

    try {
      validateForm();
      const payload = buildPayload(form);

      setIsSaving(true);

      if (selectedNodeId === "__new__" || !selectedNode) {
        await fsmAdminAPI.createNode(payload);
        setStatus({ type: "success", message: `State "${payload.id}" berhasil dibuat!` });
        setSelectedNodeId(payload.id);
      } else {
        await fsmAdminAPI.updateNode(selectedNode.id, payload);
        setStatus({ type: "success", message: `State "${payload.id}" berhasil diperbarui!` });
      }

      await fsmAdminAPI.reloadTree();
      await loadNodes(true);
      setSelectedNodeId(payload.id);
    } catch (error) {
      console.error("Gagal menyimpan state:", error);
      setStatus({ type: "error", message: error.message || "Gagal menyimpan state." });
    } finally {
      setIsSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!selectedNode || selectedNodeId === "__new__") {
      setStatus({ type: "warning", message: "Pilih state yang sudah ada sebelum menghapus." });
      return;
    }

    const confirmed = window.confirm(`Apakah Anda yakin ingin menghapus state "${selectedNode.id}"?`);
    if (!confirmed) return;

    try {
      setIsSaving(true);
      await fsmAdminAPI.deleteNode(selectedNode.id);
      await fsmAdminAPI.reloadTree();
      setStatus({ type: "success", message: `State "${selectedNode.id}" berhasil dihapus.` });
      await loadNodes(false);
    } catch (error) {
      console.error("Gagal menghapus node:", error);
      setStatus({ type: "error", message: error.message || "Gagal menghapus state." });
    } finally {
      setIsSaving(false);
    }
  };

  const handleReload = async () => {
    try {
      setIsReloading(true);
      await fsmAdminAPI.reloadTree();
      await loadNodes(true);
      setStatus({ type: "success", message: "Tree FSM berhasil di-reload dan disinkronkan." });
    } catch (error) {
      console.error("Gagal reload tree:", error);
      setStatus({ type: "error", message: error.message || "Gagal reload tree FSM." });
    } finally {
      setIsReloading(false);
    }
  };

  const getStatusIcon = (type) => {
    switch (type) {
      case "success": return <CheckCircle2 className="fsm-admin-alert-icon" size={18} />;
      case "error": return <AlertCircle className="fsm-admin-alert-icon" size={18} />;
      case "warning": return <AlertTriangle className="fsm-admin-alert-icon" size={18} />;
      default: return <Info className="fsm-admin-alert-icon" size={18} />;
    }
  };

  const getTypeIcon = (type) => {
    switch (type) {
      case "menu_state": return <Menu size={14} />;
      case "terminal_state": return <Terminal size={14} />;
      case "transitional_state": return <ArrowRightLeft size={14} />;
      default: return <Layers size={14} />;
    }
  };

  return (
    <DashboardLayout>
      <div className="fsm-admin-page">
        {/* Header Hero Section */}
        <section className="fsm-admin-hero app-card">
          <div className="fsm-admin-hero-content">
            <div className="fsm-admin-badge-hero">
              <img src={PersibLogo} alt="Persib Logo" className="hero-persib-logo" />
              <span>FSM Control Center</span>
            </div>
            <h1>State Machine Manager</h1>
            <p className="fsm-admin-subtitle">
              Kelola alur dialog MaungBot Persib, atur opsi transisi menu, dan perbarui struktur FSM secara real-time.
            </p>
          </div>

          <div className="fsm-admin-hero-actions">
            <button className="fsm-admin-primary-btn" onClick={handleNewNode}>
              <Plus size={16} />
              <span>+ State Baru</span>
            </button>
            <button
              className="fsm-admin-secondary-btn"
              onClick={handleReload}
              disabled={isReloading}
              title="Sinkronkan struktur FSM terbaru ke memori bot"
            >
              <RotateCw size={16} className={isReloading ? "spin-icon" : ""} />
              <span>{isReloading ? "Reloading..." : "Reload Tree"}</span>
            </button>
          </div>
        </section>

        {/* Stats Grid Overview */}
        <section className="fsm-admin-stats">
          <article
            className={`fsm-admin-stat app-card ${typeFilter === "all" ? "stat-active" : ""}`}
            onClick={() => setTypeFilter("all")}
          >
            <div className="fsm-admin-stat-header">
              <span>Total State</span>
              <div className="fsm-admin-stat-icon all-icon">
                <Layers size={18} />
              </div>
            </div>
            <strong>{nodes.length}</strong>
            <div className="fsm-admin-stat-footer">
              <span className="stat-subtext">Semua node terdaftar</span>
            </div>
          </article>

          <article
            className={`fsm-admin-stat app-card ${typeFilter === "menu_state" ? "stat-active" : ""}`}
            onClick={() => setTypeFilter("menu_state")}
          >
            <div className="fsm-admin-stat-header">
              <span>Menu State</span>
              <div className="fsm-admin-stat-icon menu-icon">
                <Menu size={18} />
              </div>
            </div>
            <strong>{menuCount}</strong>
            <div className="fsm-admin-stat-footer">
              <span className="stat-pct">
                {nodes.length ? Math.round((menuCount / nodes.length) * 100) : 0}% dari total
              </span>
            </div>
          </article>

          <article
            className={`fsm-admin-stat app-card ${typeFilter === "terminal_state" ? "stat-active" : ""}`}
            onClick={() => setTypeFilter("terminal_state")}
          >
            <div className="fsm-admin-stat-header">
              <span>Terminal State</span>
              <div className="fsm-admin-stat-icon terminal-icon">
                <Terminal size={18} />
              </div>
            </div>
            <strong>{terminalCount}</strong>
            <div className="fsm-admin-stat-footer">
              <span className="stat-pct">
                {nodes.length ? Math.round((terminalCount / nodes.length) * 100) : 0}% dari total
              </span>
            </div>
          </article>

          <article
            className={`fsm-admin-stat app-card ${typeFilter === "transitional_state" ? "stat-active" : ""}`}
            onClick={() => setTypeFilter("transitional_state")}
          >
            <div className="fsm-admin-stat-header">
              <span>Transitional State</span>
              <div className="fsm-admin-stat-icon trans-icon">
                <ArrowRightLeft size={18} />
              </div>
            </div>
            <strong>{transitionalCount}</strong>
            <div className="fsm-admin-stat-footer">
              <span className="stat-pct">
                {nodes.length ? Math.round((transitionalCount / nodes.length) * 100) : 0}% dari total
              </span>
            </div>
          </article>
        </section>

        {/* Status Notification Alert */}
        {status.message && (
          <div className={`fsm-admin-alert ${status.type}`}>
            {getStatusIcon(status.type)}
            <span>{status.message}</span>
            <button className="fsm-admin-alert-close" onClick={() => setStatus({ type: "info", message: "" })}>
              <X size={14} />
            </button>
          </div>
        )}

        {/* Mobile View Segmented Switcher */}
        <div className="fsm-admin-mobile-tabs">
          <button
            className={`mobile-tab-btn ${activeMobileTab === "nodes" ? "active" : ""}`}
            onClick={() => setActiveMobileTab("nodes")}
          >
            <Layers size={16} />
            <span>Daftar State ({filteredNodes.length})</span>
          </button>
          <button
            className={`mobile-tab-btn ${activeMobileTab === "editor" ? "active" : ""}`}
            onClick={() => setActiveMobileTab("editor")}
          >
            <FileText size={16} />
            <span>Editor Form</span>
          </button>
        </div>

        {/* Main Workspace Grid (Clean 2-Column Layout) */}
        <section className="fsm-admin-grid">
          {/* Panel 1: Node List Sidebar */}
          <aside className={`fsm-admin-panel app-card fsm-admin-node-list ${activeMobileTab === "nodes" ? "mobile-show" : ""}`}>
            <div className="fsm-admin-panel-header">
              <div className="panel-title-group">
                <Layers size={18} className="panel-icon" />
                <h2>Daftar Node</h2>
              </div>
              <span className="node-count-badge">{filteredNodes.length} State</span>
            </div>

            {/* Search and Type Filter Controls */}
            <div className="fsm-admin-filter-bar">
              <div className="fsm-admin-search-wrapper">
                <Search size={15} className="search-icon" />
                <input
                  type="text"
                  placeholder="Cari ID / Pesan state..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
                {searchQuery && (
                  <button className="search-clear-btn" onClick={() => setSearchQuery("")}>
                    <X size={13} />
                  </button>
                )}
              </div>

              <div className="fsm-admin-type-filters">
                <button
                  className={`filter-pill ${typeFilter === "all" ? "active" : ""}`}
                  onClick={() => setTypeFilter("all")}
                >
                  Semua
                </button>
                <button
                  className={`filter-pill ${typeFilter === "menu_state" ? "active" : ""}`}
                  onClick={() => setTypeFilter("menu_state")}
                >
                  Menu
                </button>
                <button
                  className={`filter-pill ${typeFilter === "terminal_state" ? "active" : ""}`}
                  onClick={() => setTypeFilter("terminal_state")}
                >
                  Terminal
                </button>
                <button
                  className={`filter-pill ${typeFilter === "transitional_state" ? "active" : ""}`}
                  onClick={() => setTypeFilter("transitional_state")}
                >
                  Transition
                </button>
              </div>
            </div>

            <div className="fsm-admin-node-list-body">
              {isLoading && !nodes.length ? (
                <div className="fsm-admin-empty-state">
                  <RotateCw size={24} className="spin-icon" />
                  <p>Memuat daftar state FSM...</p>
                </div>
              ) : filteredNodes.length ? (
                filteredNodes.map((node) => (
                  <button
                    key={node.id}
                    className={`fsm-admin-node-item ${selectedNodeId === node.id ? "active" : ""}`}
                    onClick={() => handleSelectNode(node.id)}
                  >
                    <div className="fsm-admin-node-item-top">
                      <strong className="node-id">{node.id}</strong>
                      <span className={`fsm-admin-badge ${node.type}`}>
                        {getTypeIcon(node.type)}
                        {formatNodeType(node.type)}
                      </span>
                    </div>
                    <p className="node-snippet">
                      {node.message || node.content || (node.action ? `Action: ${node.action}` : "Tidak ada deskripsi")}
                    </p>
                    {node.options && Object.keys(node.options).length > 0 && (
                      <div className="node-item-footer">
                        <span className="options-count">
                          <Link2 size={12} /> {Object.keys(node.options).length} cabang opsi
                        </span>
                      </div>
                    )}
                  </button>
                ))
              ) : (
                <div className="fsm-admin-empty-state">
                  <Filter size={24} />
                  <p>Tidak ada state yang cocok dengan kriteria pencarian.</p>
                </div>
              )}
            </div>
          </aside>

          {/* Panel 2: Expanded Form Editor */}
          <section className={`fsm-admin-panel app-card fsm-admin-editor ${activeMobileTab === "editor" ? "mobile-show" : ""}`}>
            <div className="fsm-admin-panel-header">
              <div className="panel-title-group">
                <Sliders size={18} className="panel-icon" />
                <h2>{selectedNodeId === "__new__" ? "Buat State Baru" : `Edit State: ${form.id}`}</h2>
              </div>
              <div className="header-meta-badges">
                <span className={`fsm-admin-badge ${form.type}`}>
                  {getTypeIcon(form.type)}
                  {formatNodeType(form.type)}
                </span>
              </div>
            </div>

            <div className="fsm-admin-form-container">
              {/* Section 1: Basic Information */}
              <div className="form-section">
                <h3 className="section-subtitle">
                  <FileText size={16} /> Informasi Utama State
                </h3>
                <div className="fsm-admin-form-grid">
                  <label className="fsm-admin-field">
                    <span className="field-label">
                      ID State <span className="required">*</span>
                    </span>
                    <input
                      type="text"
                      value={form.id}
                      onChange={(event) => handleFormChange("id", event.target.value)}
                      placeholder="Contoh: menu_jadwal_utama"
                      disabled={selectedNodeId !== "__new__" && !!selectedNode}
                    />
                    <small className="field-hint">
                      {selectedNodeId !== "__new__" && !!selectedNode
                        ? "ID State tidak dapat diubah setelah dibuat."
                        : "Gunakan huruf kecil dan underscore (contoh: menu_informasi_tiket)."}
                    </small>
                  </label>

                  <label className="fsm-admin-field">
                    <span className="field-label">
                      Tipe State <span className="required">*</span>
                    </span>
                    <select
                      value={form.type}
                      onChange={(event) => handleFormChange("type", event.target.value)}
                    >
                      {NODE_TYPES.map((type) => (
                        <option key={type.value} value={type.value}>
                          {type.label}
                        </option>
                      ))}
                    </select>
                    <small className="field-hint">
                      {NODE_TYPES.find((t) => t.value === form.type)?.description}
                    </small>
                  </label>

                  {form.type !== "terminal_state" ? (
                    <label className="fsm-admin-field fsm-admin-span-2">
                      <span className="field-label">
                        Pesan Chatbot (Message) <span className="required">*</span>
                      </span>
                      <textarea
                        rows="4"
                        value={form.message}
                        onChange={(event) => handleFormChange("message", event.target.value)}
                        placeholder={
                          form.type === "menu_state"
                            ? "Contoh: Sampurasun Bobotoh! Silakan pilih informasi yang ingin Anda ketahui..."
                            : "Contoh: Silakan masukkan nama klub lawan yang ingin Anda cari..."
                        }
                      />
                      <small className="field-hint">
                        Teks prompt / pertanyaan yang akan tampil kepada pengguna di jendela chat.
                      </small>
                    </label>
                  ) : (
                    <div className="fsm-admin-field fsm-admin-span-2 form-notice-box">
                      <small className="field-hint text-info">
                        💡 <strong>Catatan Terminal State:</strong> Teks jawaban yang tampil ke pengguna diatur oleh <code>Content</code> (jika action <code>static</code>) atau hasil query database (jika action dinamis). Field <code>message</code> tidak digunakan untuk Terminal State.
                      </small>
                    </div>
                  )}
                </div>
              </div>

              {/* Section 2: Type Specific Settings */}
              {form.type === "terminal_state" && (
                <div className="form-section">
                  <h3 className="section-subtitle">
                    <Terminal size={16} /> Konfigurasi Terminal State
                  </h3>
                  <div className="fsm-admin-form-grid">
                    <label className="fsm-admin-field">
                      <span className="field-label">
                        Action Handler <span className="required">*</span>
                      </span>
                      <SearchableSelect
                        value={form.action}
                        onChange={(val) => handleFormChange("action", val)}
                        options={DISPATCHER_ACTIONS}
                        emptyLabel="-- Pilih Action Handler --"
                      />
                      <small className="field-hint">
                        {DISPATCHER_ACTIONS.find((a) => a.value === form.action)?.description || "Pilih handler dari daftar fungsi dispatcher."}
                      </small>
                    </label>

                    <label className="fsm-admin-field">
                      <span className="field-label">
                        Kembali Ke State (Back To) <span className="required">*</span>
                      </span>
                      <SearchableSelect
                        value={form.back_to}
                        onChange={(val) => handleFormChange("back_to", val)}
                        options={selectedNodeIds}
                        emptyLabel="-- Pilih State Tujuan --"
                      />
                      <small className="field-hint">State navigasi utama tempat pengguna kembali setelah membaca respon.</small>
                    </label>

                    <label className="fsm-admin-field fsm-admin-span-2">
                      <span className="field-label">
                        Content Jawaban Statis {form.action === "static" && <span className="required">*</span>}
                      </span>
                      <textarea
                        className="static-content-textarea"
                        rows="10"
                        value={form.content}
                        onChange={(event) => handleFormChange("content", event.target.value)}
                        placeholder="Isikan teks jawaban lengkap jika Action bernilai 'static'..."
                      />
                      <small className="field-hint">Dapat diisi teks informatif panjang dengan format markdown.</small>
                    </label>
                  </div>
                </div>
              )}

              {form.type === "transitional_state" && (
                <div className="form-section">
                  <h3 className="section-subtitle">
                    <ArrowRightLeft size={16} /> Konfigurasi Transitional State
                  </h3>
                  <div className="fsm-admin-form-grid">
                    <label className="fsm-admin-field">
                      <span className="field-label">
                        Action Handler <span className="required">*</span>
                      </span>
                      <SearchableSelect
                        value={form.action}
                        onChange={(val) => handleFormChange("action", val)}
                        options={DISPATCHER_ACTIONS}
                        emptyLabel="-- Pilih Action Handler --"
                      />
                      <small className="field-hint">
                        {DISPATCHER_ACTIONS.find((a) => a.value === form.action)?.description || "Pilih handler dari daftar fungsi dispatcher."}
                      </small>
                    </label>

                    <label className="fsm-admin-field">
                      <span className="field-label">
                        Param Key <span className="required">*</span>
                      </span>
                      <input
                        type="text"
                        value={form.param_key}
                        onChange={(event) => handleFormChange("param_key", event.target.value)}
                        placeholder="Contoh: nama_lawan"
                      />
                      <small className="field-hint">Key parameter untuk menyimpan input kata kunci pengguna.</small>
                    </label>

                    <label className="fsm-admin-field fsm-admin-span-2">
                      <span className="field-label">
                        Kembali Ke State (Back To) <span className="required">*</span>
                      </span>
                      <SearchableSelect
                        value={form.back_to}
                        onChange={(val) => handleFormChange("back_to", val)}
                        options={selectedNodeIds}
                        emptyLabel="-- Pilih State Tujuan --"
                      />
                      <small className="field-hint">State tujuan navigasi setelah input diproses oleh backend.</small>
                    </label>
                  </div>
                </div>
              )}

              {form.type === "menu_state" && (
                <div className="form-section">
                  <div className="fsm-admin-options-header">
                    <div>
                      <h3 className="section-subtitle">
                        <Menu size={16} /> Pemetaan Opsi Pilihan Menu <span className="required">*</span>
                      </h3>
                      <p>Atur kecocokan angka/teks yang diinput pengguna dengan State tujuannya.</p>
                    </div>
                    <button className="fsm-admin-mini-btn primary" onClick={addOptionRow} type="button">
                      <Plus size={14} /> Tambah Opsi Baris
                    </button>
                  </div>

                  <div className="options-rows-list">
                    {form.optionsRows.map((row, index) => (
                      <div className="fsm-admin-option-row" key={`opt-${index}`}>
                        <div className="option-input-group">
                          <span className="option-num-badge">Input Pilihan #{index + 1}</span>
                          <input
                            type="text"
                            value={row.choice}
                            onChange={(event) => updateOptionRow(index, "choice", event.target.value)}
                            placeholder="Choice (ex: 1)"
                          />
                        </div>
                        <div className="option-target-group">
                          <ChevronRight size={18} className="arrow-icon" />
                          <SearchableSelect
                            value={row.target}
                            onChange={(val) => updateOptionRow(index, "target", val)}
                            options={selectedNodeIds}
                            emptyLabel="-- Pilih State Tujuan --"
                          />
                        </div>
                        <button
                          className="fsm-admin-remove-btn"
                          type="button"
                          onClick={() => removeOptionRow(index)}
                          title="Hapus opsi baris ini"
                        >
                          <Trash2 size={15} />
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Section 3: Advanced JSON Parameters */}
              <div className="form-section">
                <h3 className="section-subtitle">
                  <Code size={16} /> Dynamic Parameters (Format JSON)
                </h3>
                <label className="fsm-admin-field fsm-admin-span-2">
                  <textarea
                    rows="4"
                    className={`code-textarea ${jsonError ? "input-error" : ""}`}
                    value={form.paramsText}
                    onChange={(event) => handleFormChange("paramsText", event.target.value)}
                    placeholder='{"kompetisi": "BRI Super League", "musim": "2025/2026"}'
                  />
                  {jsonError ? (
                    <small className="field-error-msg">
                      <AlertCircle size={13} /> JSON tidak valid: {jsonError}
                    </small>
                  ) : (
                    <small className="field-hint">Konfigurasi parameter dinamis dalam format objek JSON valid.</small>
                  )}
                </label>
              </div>
            </div>

            {/* Form Actions Footer */}
            <div className="fsm-admin-actions">
              <Button onClick={handleSave} disabled={isSaving || !!jsonError}>
                <Save size={16} />
                <span>{selectedNodeId === "__new__" || !selectedNode ? "Simpan State Baru" : "Simpan Perubahan State"}</span>
              </Button>

              {selectedNode && selectedNodeId !== "__new__" && (
                <button
                  className="fsm-admin-danger-btn"
                  onClick={handleDelete}
                  disabled={isSaving}
                  type="button"
                >
                  <Trash2 size={16} />
                  <span>Hapus State</span>
                </button>
              )}
            </div>
          </section>
        </section>
      </div>
    </DashboardLayout>
  );
}

export default FsmAdmin;