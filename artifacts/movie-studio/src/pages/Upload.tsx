import { useCallback, useState } from "react";
import { Upload as UploadIcon, FileText, CheckCircle2 } from "lucide-react";
import { Card, Button, Input, Badge } from "../components/UI";
import { useUpload } from "../hooks/use-upload";
import { useUploadStore } from "../stores/appStore";

export default function Upload() {
  const { file, metadata, uploadHistory, setFile, setMetadata, resetMetadata, addToHistory } = useUploadStore();
  const { upload, progress, isUploading, error } = useUpload();
  const [success, setSuccess] = useState(false);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    const droppedFile = e.dataTransfer.files[0];
    const allowedExts = ['.txt', '.md', '.pdf', '.png', '.jpg', '.jpeg'];
    if (droppedFile && allowedExts.some(ext => droppedFile.name.toLowerCase().endsWith(ext))) {
      setFile(droppedFile);
      setSuccess(false);
    } else {
      alert("Supported formats: .txt, .md, .pdf, .png, .jpg, .jpeg");
    }
  }, [setFile]);

  const handleUpload = async () => {
    if (!file) return;
    setSuccess(false);
    const formData = new FormData();
    formData.append("file", file);
    Object.entries(metadata).forEach(([k, v]) => {
      if (v) formData.append(k, v);
    });

    try {
      const res = await upload(formData);
      addToHistory({
        filename: res.data?.filename || file.name,
        chunk_count: res.data?.chunk_count || 0,
        status: res.data?.status || "completed",
        timestamp: Date.now(),
      });
      resetMetadata();
      setSuccess(true);
    } catch {
      setSuccess(false);
    }
  };

  return (
    <div className="p-6 md:p-10 max-w-6xl mx-auto">
      <div className="mb-10">
        <h2 className="text-3xl font-display font-bold text-white mb-2">Ingest Documents</h2>
        <p className="text-muted-foreground">Upload screenplays, reviews, and analysis to the vector store.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="space-y-6">
          <Card 
            className={`p-10 border-2 border-dashed flex flex-col items-center justify-center text-center transition-colors cursor-pointer ${file ? 'border-primary bg-primary/5' : 'border-white/20 hover:border-primary/50'}`}
            onDragOver={(e) => e.preventDefault()}
            onDrop={handleDrop}
            onClick={() => document.getElementById('file-upload')?.click()}
          >
            <input type="file" id="file-upload" className="hidden" accept=".txt,.md,.pdf,.png,.jpg,.jpeg,image/png,image/jpeg,application/pdf" onChange={(e) => { setFile(e.target.files?.[0] || null); setSuccess(false); }} />
            <div className={`p-4 rounded-full mb-4 ${file ? 'bg-primary text-primary-foreground' : 'bg-white/5 text-muted-foreground'}`}>
              <UploadIcon className="w-8 h-8" />
            </div>
            {file ? (
              <>
                <p className="text-lg font-medium text-white mb-1">{file.name}</p>
                <p className="text-sm text-primary">{(file.size / 1024).toFixed(1)} KB</p>
              </>
            ) : (
              <>
                <p className="text-lg font-medium text-white mb-1">Drag & drop document here</p>
                <p className="text-sm text-muted-foreground">Supports .txt, .md, .pdf, .png, .jpg, .jpeg</p>
              </>
            )}
          </Card>

          <Card className="p-6">
            <h3 className="text-lg font-semibold text-white mb-4">Document Metadata</h3>
            <div className="space-y-4">
              <div>
                <label className="text-sm text-muted-foreground mb-1.5 block">Movie Title</label>
                <Input value={metadata.movie_title} onChange={e => setMetadata({ movie_title: e.target.value })} placeholder="e.g. Dune: Part Two" />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm text-muted-foreground mb-1.5 block">Source Type</label>
                  <select 
                    className="flex h-12 w-full rounded-xl border border-white/10 bg-black/40 px-4 py-2 text-sm text-white focus:outline-none focus:border-primary/50"
                    value={metadata.source_type} onChange={e => setMetadata({ source_type: e.target.value })}
                  >
                    <option value="document">Document</option>
                    <option value="review">Review</option>
                    <option value="analysis">Analysis</option>
                    <option value="timeline">Timeline</option>
                    <option value="script">Screenplay</option>
                  </select>
                </div>
                <div>
                  <label className="text-sm text-muted-foreground mb-1.5 block">Release Year</label>
                  <Input type="number" value={metadata.release_year} onChange={e => setMetadata({ release_year: e.target.value })} placeholder="2024" />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm text-muted-foreground mb-1.5 block">Director</label>
                  <Input value={metadata.director} onChange={e => setMetadata({ director: e.target.value })} placeholder="e.g. Denis Villeneuve" />
                </div>
                <div>
                  <label className="text-sm text-muted-foreground mb-1.5 block">Franchise</label>
                  <Input value={metadata.franchise} onChange={e => setMetadata({ franchise: e.target.value })} placeholder="e.g. Marvel, DC, Dune" />
                </div>
              </div>

              {isUploading && (
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">
                      {progress.percent < 100 ? "Uploading..." : "Processing document..."}
                    </span>
                    <span className="text-primary font-mono">{progress.percent}%</span>
                  </div>
                  <div className="w-full bg-white/10 h-2 rounded-full overflow-hidden">
                    <div 
                      className="bg-primary h-full rounded-full transition-all duration-300" 
                      style={{ width: `${progress.percent}%` }} 
                    />
                  </div>
                  {progress.total > 0 && (
                    <p className="text-xs text-muted-foreground">
                      {(progress.loaded / 1024).toFixed(1)} / {(progress.total / 1024).toFixed(1)} KB
                    </p>
                  )}
                </div>
              )}

              <Button onClick={handleUpload} disabled={!file || isUploading} className="w-full mt-4 py-6 text-lg">
                {isUploading ? "Ingesting..." : "Ingest to Vector Store"}
              </Button>
              {error && <p className="text-red-400 text-sm mt-2 text-center">{error}</p>}
              {success && !isUploading && (
                <p className="text-green-400 text-sm mt-2 text-center flex items-center justify-center gap-1">
                  <CheckCircle2 className="w-4 h-4" /> Document ingested successfully!
                </p>
              )}
            </div>
          </Card>
        </div>

        <div>
          <h3 className="text-lg font-semibold text-white mb-4">Ingestion History</h3>
          <div className="space-y-3">
            {uploadHistory.length === 0 ? (
              <Card className="p-8 text-center text-muted-foreground border-dashed">No recent uploads</Card>
            ) : (
              uploadHistory.map((job, i) => (
                <Card key={i} className="p-4 flex items-center gap-4">
                  <div className="bg-green-500/20 text-green-400 p-2 rounded-lg">
                    <FileText className="w-5 h-5" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-white font-medium truncate">{job.filename}</p>
                    <p className="text-xs text-muted-foreground mt-0.5">Chunks generated: {job.chunk_count}</p>
                  </div>
                  <Badge variant="success" className="capitalize">{job.status}</Badge>
                </Card>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
