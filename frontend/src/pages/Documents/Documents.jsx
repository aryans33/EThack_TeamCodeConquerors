import { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { docAPI } from '../../services/api';
import { Upload, FileText, CheckCircle, XCircle, Clock } from 'lucide-react';
import './Documents.css';

const STATUS_ICON = {
    processing: <Clock size={14} style={{ color: 'var(--warning)' }} />,
    ready: <CheckCircle size={14} style={{ color: 'var(--profit)' }} />,
    error: <XCircle size={14} style={{ color: 'var(--loss)' }} />,
};

export default function Documents() {
    const [files, setFiles] = useState([]);
    const [symbol, setSymbol] = useState('');
    const [uploads, setUploads] = useState([]);

    const onDrop = useCallback((accepted) => {
        setFiles((prev) => [...prev, ...accepted]);
    }, []);

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop, accept: { 'application/pdf': ['.pdf'] }, multiple: true,
    });

    const handleUpload = async () => {
        if (!files.length) return;
        for (const file of files) {
            const id = Date.now() + Math.random();
            setUploads((prev) => [...prev, { id, name: file.name, symbol, status: 'processing', progress: 0 }]);
            try {
                const fd = new FormData();
                fd.append('file', file);
                if (symbol) fd.append('symbol', symbol.toUpperCase());
                fd.append('document_type', 'annual_report');
                await docAPI.upload(fd);
                setUploads((prev) => prev.map((u) => u.id === id ? { ...u, status: 'ready', progress: 100 } : u));
            } catch {
                setUploads((prev) => prev.map((u) => u.id === id ? { ...u, status: 'error' } : u));
            }
        }
        setFiles([]);
    };

    return (
        <div className="documents-page fade-in">
            <div className="page-title-row">
                <h1>Documents</h1>
                <p>Upload annual reports, concall transcripts, and fund reports for AI analysis</p>
            </div>

            <div className="documents-grid">
                {/* Upload Card */}
                <div className="card upload-card">
                    <div className="card-header"><span className="flex items-center gap-8"><Upload size={16} /> Upload PDFs</span></div>
                    <div className="card-body">
                        <div {...getRootProps()} className={`upload-zone ${isDragActive ? 'active' : ''}`}>
                            <input {...getInputProps()} />
                            <FileText size={40} style={{ color: 'var(--text-muted)', marginBottom: 12 }} />
                            {isDragActive
                                ? <p>Drop PDFs here…</p>
                                : <><p>Drag & drop PDFs here</p><p style={{ fontSize: '0.8rem', marginTop: 8, color: 'var(--text-muted)' }}>or click to browse</p></>
                            }
                        </div>

                        {files.length > 0 && (
                            <div className="file-list">
                                {files.map((f, i) => (
                                    <div key={i} className="file-item">
                                        <FileText size={14} style={{ color: 'var(--accent)' }} />
                                        <span>{f.name}</span>
                                        <span style={{ marginLeft: 'auto', color: 'var(--text-muted)', fontSize: '0.75rem' }}>
                                            {(f.size / 1024).toFixed(0)} KB
                                        </span>
                                    </div>
                                ))}
                            </div>
                        )}

                        <div className="input-group" style={{ marginTop: 16 }}>
                            <label className="input-label">Stock Symbol (optional)</label>
                            <input className="input" placeholder="e.g. TCS, RELIANCE" value={symbol}
                                onChange={(e) => setSymbol(e.target.value.toUpperCase())} />
                        </div>

                        <button className="btn btn-primary" style={{ marginTop: 12, width: '100%', justifyContent: 'center' }}
                            onClick={handleUpload} disabled={!files.length}>
                            <Upload size={14} /> Upload {files.length > 0 ? `${files.length} file${files.length > 1 ? 's' : ''}` : ''}
                        </button>
                    </div>
                </div>

                {/* Status Card */}
                <div className="card">
                    <div className="card-header">
                        <span>Upload History</span>
                        <span className="badge badge-info">{uploads.length}</span>
                    </div>
                    <div className="card-body" style={{ padding: 0 }}>
                        {uploads.length === 0
                            ? <div className="empty-state"><FileText size={32} /><p>No uploads yet</p></div>
                            : uploads.map((u) => (
                                <div key={u.id} className="upload-status-row">
                                    <FileText size={14} style={{ color: 'var(--text-muted)' }} />
                                    <div className="upload-name">
                                        <span>{u.name}</span>
                                        {u.symbol && <span className="badge badge-muted" style={{ marginLeft: 8 }}>{u.symbol}</span>}
                                    </div>
                                    <div className="upload-status">{STATUS_ICON[u.status]} {u.status}</div>
                                </div>
                            ))
                        }
                    </div>
                </div>
            </div>

            {/* Info */}
            <div className="card info-card" style={{ marginTop: 20 }}>
                <div className="card-body" style={{ display: 'flex', gap: 24, flexWrap: 'wrap' }}>
                    {[
                        { title: 'Step 1: Upload', desc: 'Upload PDF — Mistral OCR extracts text into JSON chunks' },
                        { title: 'Step 2: Vectorize', desc: 'Gemini embeddings store chunks in ChromaDB vector store' },
                        { title: 'Step 3: Analyze', desc: 'AI agents search relevant chunks during stock analysis' },
                    ].map(({ title, desc }) => (
                        <div key={title} className="info-step">
                            <div className="info-step-title">{title}</div>
                            <div className="info-step-desc">{desc}</div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}
