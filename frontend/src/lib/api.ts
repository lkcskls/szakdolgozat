import { FileTableData } from "@/components/file-table";

export const BACKEND_BASE_URL = "http://localhost:8000";


export async function getFiles(): Promise<FileTableData[]> {
    const res = await fetch(`${BACKEND_BASE_URL}/api/files`, {
        method: 'GET',
        credentials: 'include',
    });
    return await res.json();
};

export const uploadFiles = async (files: File[], encrypted: boolean) => {
    if (files.length === 0) return;

    const formData = new FormData();
    files.forEach((file) => {
        formData.append("files", file);
    });

    const res = await fetch(`${BACKEND_BASE_URL}/api/upload?encrypted=${encrypted}`, {
        method: "POST",
        body: formData,
        credentials: "include",
    });

    const result = await res.json();
    //console.log(result)

    if (!res.ok) {
        throw new Error(result.detail || "Upload failed");
    }
};


export const registerUser = async (name: string, email: string, secondEmail: string, password: string) => {
    const res = await fetch(`${BACKEND_BASE_URL}/api/register`, {
        method: "POST",
        credentials: 'include',
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: name, email: email, second_email: secondEmail, password: password }),
    });
    if (!res.ok) throw new Error("Regisztrációs hiba");
    return res.json();
};

export const loginUser = async (email: string, password: string) => {
    const res = await fetch(`${BACKEND_BASE_URL}/api/login`, {
        method: "POST",
        credentials: 'include',
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
    });
    if (!res.ok) throw new Error("Bejelentkezési hiba");
    return res.json();
};

export const logoutUser = async () => {
    const res = await fetch(`${BACKEND_BASE_URL}/api/logout`, { method: "POST" });
    if (!res.ok) throw new Error("Kijelentkezési hiba");
    return res.json();
};

export const getUser = async () => {
    const res = await fetch(`${BACKEND_BASE_URL}/api/user`, {
        method: "GET",
        credentials: 'include'
    });
    if (!res.ok) throw new Error("Felhasználó lekérés hiba");
    return res.json();
};

export const editUser = async (updateData: {
    name?: string;
    email?: string;
    second_email?: string;
    password?: string;
    algo?: string;
}) => {
    const query = new URLSearchParams();
    if (updateData.name) query.append("name", updateData.name);
    if (updateData.email) query.append("email", updateData.email);
    if (updateData.second_email) query.append("second_email", updateData.second_email);
    if (updateData.password) query.append("password", updateData.password);
    if (updateData.algo) query.append("algo", updateData.algo);

    const res = await fetch(`${BACKEND_BASE_URL}/api/user?${query.toString()}`, {
        method: "PUT",
        credentials: 'include'
    });
    if (!res.ok) throw new Error("Felhasználó szerkesztési hiba");
    return res.json();
};

export const downloadFileByName = async (filename: string) => {
    const res = await fetch(`${BACKEND_BASE_URL}/api/download?filename=${filename}`, {
        method: "GET",
        credentials: 'include'
    });
    if (!res.ok) throw new Error("Letöltési hiba");

    

    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    window.open(url, "_blank");
    // return res.blob(); // vagy res.json() ha JSON választ vársz
};

export const downloadFileByUuid = async (uuid: string) => {
    const res = await fetch(`${BACKEND_BASE_URL}/api/download?uuid=${uuid}`, {
        method: "GET",
        credentials: 'include'
    });
    if (!res.ok) throw new Error("Letöltési hiba");
    return res.blob(); // vagy res.json() ha JSON választ vársz
};

export const deleteFileByName = async (filename: string) => {
    const res = await fetch(`${BACKEND_BASE_URL}/api/files?filename=${filename}`, {
        method: "DELETE",
        credentials: 'include'
    });



    return await res.json();
};

export const deleteFileByUuid = async (uuid: string) => {
    const res = await fetch(`${BACKEND_BASE_URL}/api/files?uuid=${uuid}`, {
        method: "DELETE",
        credentials: 'include'
    });

    return await res.json();
};
