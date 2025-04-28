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

export type UserEncDetailsResponse = {
    algo: string;
    hasSecretKey: boolean;
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
        throw new Error(result.detail || "Failed to sign up");
    }

    toast("Registration successful")
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
        throw new Error(result.detail || "Failed to log in");
    }

    toast("Loged in successfully")
    return result;
};

export const logoutUser = async () => {
    const res = await fetch(`${BACKEND_BASE_URL}/api/logout`, {
        method: "POST",
        credentials: "include"
    });
    if (!res.ok) {
        toast("Log out failed")
        throw new Error("Log out failed");
    }

    toast("Loged out successfully")
    return res.json();
};

export async function getUser(): Promise<User> {
    const res = await fetch(`${BACKEND_BASE_URL}/api/user`, {
        method: "GET",
        credentials: 'include'
    });
    const result = await res.json();

    if (!res.ok) {
        toast(result.detail || "Failed to fetch user data");
        throw new Error(result.detail || "Failed to fetch user data");
    }
    return result;
};

export const editUser = async (updateData: {
    name?: string;
    email?: string;
    password?: string;
    newPassword?: string;
}) => {
    const query = new URLSearchParams();
    if (updateData.name) query.append("name", updateData.name);
    if (updateData.email) query.append("email", updateData.email);
    if (updateData.password) query.append("password", updateData.password);
    if (updateData.newPassword) query.append("new_password", updateData.newPassword);

    const res = await fetch(`${BACKEND_BASE_URL}/api/user?${query.toString()}`, {
        method: "PUT",
        credentials: 'include'
    });

    const result = await res.json();

    if (!res.ok) {
        toast(result.detail || "Failed to update user");
        throw new Error(result.detail || "Failed to update user");
    }
    toast("Profile updated successfully");
    return result;
};

export async function getFiles(): Promise<FileTableData[]> {
    const res = await fetch(`${BACKEND_BASE_URL}/api/files`, {
        method: 'GET',
        credentials: 'include',
    });
    const result = await res.json();

    if (!res.ok) {
        toast(result.detail || "Failed to fetch files");
        throw new Error(result.detail || "Failed to fetch files");
    }

    return result;
};

export const deleteFileByName = async (filename: string, key_hex: string) => {
    const res = await fetch(`${BACKEND_BASE_URL}/api/files?filename=${filename}&key_hex=${key_hex}`, {
        method: "DELETE",
        credentials: 'include'
    });
    const result = await res.json();

    if (!res.ok) {
        toast(result.detail || "Failed to delete file");
        throw new Error(result.detail || "Failed to delete file");
    }

    toast("File deleted successfully")
    return result;
};

export const uploadFiles = async (files: File[], encrypted: boolean, keyHex: string) => {
    if (files.length === 0) return;

    //fájlméret ellenőrzése
    const maxTotalSize = MAX_UPLOAD_SIZE * 1024 * 1024;
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

    if (!res.ok) {
        toast("Failed to upload files");
        throw new Error("Failed to upload files");
    }

    toast("Files processed successfully")
    return result;
};

export const downloadFileByName = async (filename: string, keyHex: string) => {
    console.log(filename, keyHex)
    const res = await fetch(`${BACKEND_BASE_URL}/api/download?filename=${filename}&key_hex=${keyHex}`, {
        method: "GET",
        credentials: 'include'
    });

    if (!res.ok) {
        const result = await res.json();
        toast(result.detail || "Failed to open file");
        throw new Error(result.detail || "Failed to open file");
    }

    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    window.open(url, "_blank");
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

export async function getUserEncDetails(): Promise<UserEncDetailsResponse> {
    const res = await fetch(`${BACKEND_BASE_URL}/api/encrypt-details`, {
        method: "GET",
        credentials: "include",
    });
    const result = await res.json();

    if (!res.ok) {
        toast(result.detail || "Failed to fetch user's encryption details");
        throw new Error(result.detail || "Failed to fetch user's encryption details");
    }

    const data: UserEncDetailsResponse = result;
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
    const result = await res.json();

    if (!res.ok) {
        toast(result.detail || "Failed to change algorithm");
        throw new Error(result.detail || "Failed to change algorithm");
    }

    toast(result.message)
    return result;
};

export const genSecretKey = async (key_hex: string) => {
    const res = await fetch(`${BACKEND_BASE_URL}/api/gen-sk?current-sk=${key_hex}`, {
        method: "GET",
        credentials: "include"
    });
    const result = await res.json();

    if (!res.ok) {
        toast(result.detail || "Failed to generat secret key");
        throw new Error(result.detail || "Failed to generat secret key");
    }

    toast("Secret key generated successfully")
    return result;
};

export async function verifySecretKey(keyHex: string): Promise<boolean> {
    try {
        const res = await fetch(`${BACKEND_BASE_URL}/api/verify-secret-key?key_hex=${keyHex}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include',
        });
        const result = await res.json();

        if (!res.ok) {
            toast(result.detail || "Failed to verify secret key");
            throw new Error(result.detail || "Failed to verify secret key");
        }

        return result;
    } catch {
        return false;
    }
};
