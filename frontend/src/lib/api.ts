import { FileTableData } from "@/components/file-table";
import { toast } from 'sonner'


export const BACKEND_BASE_URL = "https://localhost";
const MAX_UPLOAD_SIZE = 500 //Mb


export type User = {
    id: number
    name: string
    email: string
    algo: string
};

export type UserAlgoResponse = {
    algo: string;
    hasSecretKey: boolean;
};

export async function getFiles(): Promise<FileTableData[]> {
    const res = await fetch(`${BACKEND_BASE_URL}/api/files`, {
        method: 'GET',
        credentials: 'include',
    });
    if (!res.ok) {
        toast("Failed to fetch files")
    }
    return await res.json();
};

export const uploadFiles = async (files: File[], encrypted: boolean, keyHex: string) => {
    if (files.length === 0) return;

    //fájlméret ellenőrzése
    const maxTotalSize = MAX_UPLOAD_SIZE * 1024 * 1024; // 500 MB byte-ban
    const totalSize = files.reduce((acc, file) => acc + file.size, 0);
    if (totalSize > maxTotalSize) {
        toast("Total file size exceeds 500 MB limit");
        throw new Error("Total file size exceeds 500 MB");
    }

    const formData = new FormData();
    files.forEach((file) => {
        formData.append("files", file);
    });

    const res = await fetch(`${BACKEND_BASE_URL}/api/upload?encrypted=${encrypted}&key_hex=${keyHex}`, {
        method: "POST",
        body: formData,
        credentials: "include",
    });

    const result = await res.json();

    toast("Files processed successfully")
    return result;
};

export const registerUser = async (name: string, email: string, password: string) => {
    const res = await fetch(`${BACKEND_BASE_URL}/api/register`, {
        method: "POST",
        credentials: 'include',
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: name, email: email, password: password }),
    });

    const result = await res.json();

    if (!res.ok) {
        toast(result.detail || "Failed to sign up");
        throw new Error("Failed to sign up");
    }

    return result;
};

export const loginUser = async (email: string, password: string) => {
    const res = await fetch(`${BACKEND_BASE_URL}/api/login`, {
        method: "POST",
        credentials: 'include',
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
    });
    const result = await res.json();

    if (!res.ok) {
        toast(result.detail || "Failed to log in");
        throw new Error("Login failed");
    }

    return result;
};

export const logoutUser = async () => {
    const res = await fetch(`${BACKEND_BASE_URL}/api/logout`, {
        method: "POST",
        credentials: "include"
    });
    if (!res.ok) {
        toast("Logout failed")
        throw new Error("Logout failed");
    }
    return res.json();
};

export async function getUser(): Promise<User> {
    const res = await fetch(`${BACKEND_BASE_URL}/api/user`, {
        method: "GET",
        credentials: 'include'
    });
    if (!res.ok) {
        toast("Failed to fetch user data")
        throw new Error("Failed to fetch user data");
    }
    return res.json();
};

export const editUser = async (updateData: {
    name?: string;
    email?: string;
    password?: string;
}) => {
    const query = new URLSearchParams();
    if (updateData.name) query.append("name", updateData.name);
    if (updateData.email) query.append("email", updateData.email);
    if (updateData.password) query.append("password", updateData.password);

    const res = await fetch(`${BACKEND_BASE_URL}/api/user?${query.toString()}`, {
        method: "PUT",
        credentials: 'include'
    });

    const result = await res.json();

    if (!res.ok) {
        toast(result.detail || "Failed to update user");
        throw new Error("Failed to update user");
    }
    toast("Profile updated successfully");
    return result;
};

export const downloadFileByName = async (filename: string, keyHex: string) => {
    console.log(filename, keyHex)
    const res = await fetch(`${BACKEND_BASE_URL}/api/download?filename=${filename}&key_hex=${keyHex}`, {
        method: "GET",
        credentials: 'include'
    });
    console.log(res)
    if (!res.ok) {
        const result = await res.json();
        toast(result.detail || "Failed to open file");
        throw new Error("Failed to open file");
    }
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    window.open(url, "_blank");
};

export const deleteFileByName = async (filename: string) => {
    const res = await fetch(`${BACKEND_BASE_URL}/api/files?filename=${filename}`, {
        method: "DELETE",
        credentials: 'include'
    });
    if (!res.ok) {
        const result = await res.json();
        toast(result.detail || "Failed to delete file");
        throw new Error("Failed to delete file");
    }
    return await res.json();
};

export async function getAlgos() {
    const res = await fetch(`${BACKEND_BASE_URL}/api/algos`, {
        method: "GET",
        credentials: "include",
    });
    if (!res.ok) {
        toast("Failed to fetch algorithms")
        throw new Error("Failed to fetch algorithms");
    }
    return res.json();
};

export async function getUserAlgo(): Promise<UserAlgoResponse> {
    const res = await fetch(`${BACKEND_BASE_URL}/api/algo`, {
        method: "GET",
        credentials: "include",
    });
    if (!res.ok) {
        toast("Failed to fetch user's algorithm")
        throw new Error("Failed to fetch user's algorithm");
    }
    const data: UserAlgoResponse = await res.json();
    return data;
};

export const changeAlgorithm = async (newAlgo: string, key_hex: string) => {
    const res = await fetch(`${BACKEND_BASE_URL}/api/switch-algo`, {
        method: 'POST',
        credentials: 'include',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            algo: newAlgo,
            key_hex: key_hex
        }),
    });

    if (!res.ok) {
        const result = await res.json();
        toast(result.detail || "Failed to change algorithm");
        console.error('Failed to change algorithm to', newAlgo);
        throw new Error('Failed to change algorithm');
    }

    const data = await res.json();
    console.log(data.message);
    toast(data.message)
    return data;
};

export const genSecretKey = async (key_hex: string) => {
    const res = await fetch(`${BACKEND_BASE_URL}/api/gen-sk?current-sk=${key_hex}`, {
        method: "GET",
        credentials: "include"
    });
    if (!res.ok) {
        toast("Failed to generat secret key")
        throw new Error("Failed to generat secret key");
    }
    return res.json();
};

export async function verifySecretKey(keyHex: string): Promise<boolean> {
    try {
        // Lekérés a FastAPI végpontra
        const response = await fetch(`${BACKEND_BASE_URL}/api/verify-secret-key?key_hex=${keyHex}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include',
        });

        // Ellenőrizzük, hogy a válasz sikeres volt-e
        if (!response.ok) {
            toast("Failed to verify secret key")
            throw new Error('Failed to verify secret key');
        }

        // Válasz JSON elemzése
        const data = await response.json();

        // Feltételezve, hogy a válasz egy boolean érték
        return data;
    } catch (error) {
        console.error('Failed to verify secret key:', error);
        return false; // Hibás válasz esetén false-t adunk vissza
    }
};
