import { FileTableData } from "@/components/file-table";
import { toast } from 'sonner'

//user key_hex = "cae9b6905136901b9f17fc6389fbdf9e00d10fb05ffcdf40e98f45014ee5fdcc"

export const BACKEND_BASE_URL = "https://localhost";

export type User = {
    id: number
    name: string
    email: string
    second_email: string
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
        toast("Upload failed")
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
    if (!res.ok) {
        toast("Failed to sign up")
        throw new Error("Failed to sign up");
    }
    return res.json();
};

export const loginUser = async (email: string, password: string) => {
    const res = await fetch(`${BACKEND_BASE_URL}/api/login`, {
        method: "POST",
        credentials: 'include',
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
    });
    if (!res.ok) {
        toast("Invalid email or password")
        throw new Error("Login failed");
    }
    return res.json();
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
    if (!res.ok) {
        toast("Failed to update user")
        throw new Error("Failed to update user");
    }
    return res.json();
};

export const downloadFileByName = async (filename: string, keyHex: string) => {
    console.log(filename, keyHex)
    const res = await fetch(`${BACKEND_BASE_URL}/api/download?filename=${filename}&key_hex=${keyHex}`, {
        method: "GET",
        credentials: 'include'
    });
    console.log(res)
    if (!res.ok) {
        toast("File could not be opened. Your secret key might be invalid.")
        throw new Error("File could not be opened. Your secret key might be invalid.");
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
        toast("Failed to delete file")
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
    try {
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
            throw new Error('Failed to change algorithm');
        }

        const data = await res.json();
        console.log('Algorithm changed:', data.message);
        return data;
    } catch (err) {
        toast("Failed to change algorithm ")
        console.error('Failed to change algorithm:', err);
        throw err; // A hiba továbbadásához
    }
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
}
