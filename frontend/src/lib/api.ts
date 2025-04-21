import { FileTableData } from "@/components/file-table";
import { toast } from 'sonner'

export const BACKEND_BASE_URL = "http://localhost:8000";

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
    const res = await fetch(`${BACKEND_BASE_URL}/api/logout`, {
        method: "POST",
        credentials: "include"
    });
    if (!res.ok) throw new Error("Kijelentkezési hiba");
    return res.json();
};

export async function getUser(): Promise<User> {
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

export const downloadFileByName = async (filename: string, keyHex: string) => {
    console.log(filename, keyHex)
    const res = await fetch(`${BACKEND_BASE_URL}/api/download?filename=${filename}&key_hex=${keyHex}`, {
        method: "GET",
        credentials: 'include'
    });
    console.log(res)
    if (!res.ok) {
        toast("File can't be shown, maybe your secret key is invalid")
        throw new Error("File can't be shown, maybe your secret key is invalid");
    }
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

export async function getAlgos() {
    const res = await fetch(`${BACKEND_BASE_URL}/api/algos`, {
        method: "GET",
        credentials: "include",
    });
    if (!res.ok) {
        toast("Problem with fetching the algos")
        throw new Error("Problem with fetching the algos");
    }
    return res.json();
};

export async function getUserAlgo(): Promise<UserAlgoResponse> {
    const res = await fetch(`${BACKEND_BASE_URL}/api/algo`, {
        method: "GET",
        credentials: "include",
    });
    if (!res.ok) {
        toast("Problem with fetching the algos")
        throw new Error("Problem with fetching the algos");
    }
    const data: UserAlgoResponse = await res.json();
    return data;
};

export const changeAlgorithm = async (newAlgo: string, secretKey: string) => {
    try {
        const res = await fetch(`${BACKEND_BASE_URL}/api/switch-algo`, {
            method: 'POST',
            credentials: 'include', // Biztosítja a session cookie-kat
            headers: {
                'Content-Type': 'application/json', // JSON típusú adatot küldünk
            },
            body: JSON.stringify({
                algo: newAlgo, // A kívánt algoritmus
                current_sk: secretKey
            }),
        });

        if (!res.ok) {
            throw new Error('Failed to change algorithm');
        }

        const data = await res.json();
        console.log('Algorithm changed:', data.message);
        return data;
    } catch (err) {
        toast("Failed to change algorithm")
        console.error('Error changing algorithm:', err);
        throw err; // A hiba továbbadásához
    }
};


