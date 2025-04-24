import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Switch } from "./ui/switch";
import { FaTrash } from "react-icons/fa";  // Szemetes ikon importálása
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { uploadFiles } from "@/lib/api";
import { useKey } from "./KeyProvider";
import { toast } from "sonner";

interface FileUploadModalProps {
    onUploadComplete: () => void
}

type UploadResult = {
    file: string;
    status: "uploaded" | "failed";
    error: string;
};

export default function FileUploadModal({ onUploadComplete }: FileUploadModalProps) {
    const [isOpen, setIsOpen] = useState(false);
    const [files, setFiles] = useState<File[]>([]); // Több fájl kezelése
    const [encrypted, setEncrypted] = useState(false);
    const [isUploading, setIsUploading] = useState(false);
    const { keyHex, setKeyHex } = useKey();

    const [uploadResults, setUploadResults] = useState<UploadResult[] | null>(null);
    const [resultDialogOpen, setResultDialogOpen] = useState(false);

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files) {
            // Több fájl hozzáadása a listához
            const newFiles = Array.from(e.target.files);
            setFiles((prevFiles) => [...prevFiles, ...newFiles]);
        }
        const fileInput = document.getElementById('file-upload') as HTMLInputElement;
        if (fileInput) {
            fileInput.value = ''; // Reset the input field
        }
    };

    const handleFileRemove = (fileToRemove: File) => {
        setFiles((prevFiles) => prevFiles.filter((file) => file !== fileToRemove));
    };

    const handleClearInput = () => {
        const fileInput = document.getElementById('file-upload') as HTMLInputElement;
        if (fileInput) {
            fileInput.value = ''; // Reset the input field
        }
        setFiles([]); // Clear the files from state
    };

    const handleUpload = async () => {
        if (files.length === 0) return;
        setIsUploading(true);

        try {
            const result = await uploadFiles(files, encrypted, keyHex);
            setUploadResults(result);          //eredmények mentése
            setResultDialogOpen(true);

            setIsOpen(false);  //bezárja a modált sikeres feltöltés után
            setFiles([]);  //feltöltés után töröljük a fájlokat
            onUploadComplete();
        } catch (err) {
            console.error("Upload failed", err);
        } finally {
            setIsUploading(false);
        }
    };

    return (
        <>
            <Dialog open={isOpen} onOpenChange={setIsOpen}>
                <DialogTrigger asChild>
                    <Button variant="default">Upload File</Button>
                </DialogTrigger>

                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>Upload File</DialogTitle>
                    </DialogHeader>

                    <i className="text-xs"><p>Upload limit is 500 Mb/upload <br />
                        Your filenames must be uniqe</p></i>

                    {isUploading ? (
                        <p>Uploading...</p>
                    ) : (
                        <>
                            <Input
                                type="file"
                                id="file-upload"
                                multiple
                                onChange={handleFileChange}
                            />

                            <div className="mt-4">
                                {files.length > 0 && files.length < 11 && (
                                    <ul>
                                        {files.map((file, index) => (
                                            <li key={index} className="flex items-center justify-between">
                                                <span>{file.name}</span>
                                                <button
                                                    type="button"
                                                    onClick={() => handleFileRemove(file)}
                                                    style={{
                                                        background: 'none',
                                                        border: 'none',
                                                        color: 'black',
                                                        cursor: 'pointer',
                                                    }}
                                                >
                                                    ✖️
                                                </button>
                                            </li>
                                        ))}
                                    </ul>
                                )}
                                {files.length > 10 && (
                                    <p className="text-center">{files.length} files selected</p>
                                )}
                            </div>
                            {files.length > 0 ? <>
                                <Button onClick={handleClearInput}>Clear Files</Button>
                            </> : <></>}

                            <div className="flex items-center space-x-2">
                                <Switch
                                    id="encrypted-toggle"
                                    checked={encrypted}
                                    onCheckedChange={(checked) => setEncrypted(checked)}
                                />
                                <Label htmlFor="encrypted-toggle">File encryption</Label>
                            </div>
                            {encrypted ? <>
                                <Label htmlFor="key_hex">Your secret key:</Label>
                                <Input id="key_hex" type="text" value={keyHex} onChange={(e) => { setKeyHex(e.target.value) }} />
                            </> : <></>}

                            <DialogFooter>
                                <Button variant="secondary" onClick={() => { setIsOpen(false); setFiles([]); }}>
                                    Cancel
                                </Button>
                                <Button variant="default" onClick={handleUpload}>
                                    Upload
                                </Button>
                            </DialogFooter>
                        </>
                    )}
                </DialogContent>
            </Dialog>
            <Dialog open={resultDialogOpen} onOpenChange={setResultDialogOpen}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>Upload results</DialogTitle>
                    </DialogHeader>

                    {uploadResults && (
                        <ul className="space-y-2 mt-2">
                            {uploadResults.map((res, idx) => (
                                <li key={idx} className="text-sm">
                                    <span className={res.status === "uploaded" ? "text-green-600" : "text-red-600"}>
                                        {res.status === "uploaded" ? "✔️" : "✖️"} {res.file}
                                    </span>
                                    {res.error && (
                                        <p className="text-xs text-muted-foreground ml-4">Error: {res.error}</p>
                                    )}
                                </li>
                            ))}
                        </ul>
                    )}

                    <DialogFooter>
                        <Button onClick={() => setResultDialogOpen(false)}>Close</Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </>
    );
}
