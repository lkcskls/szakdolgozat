"use client";

import { createContext, useContext, useState } from "react";

type KeyContextType = {
    keyHex: string;
    setKeyHex: (key: string) => void;
};

export const KeyContext = createContext<KeyContextType | undefined>(undefined);

export const useKey = () => {
    const context = useContext(KeyContext);
    if (!context) {
        throw new Error("useKey must be used within a KeyProvider");
    }
    return context;
};

export const KeyProvider = ({ children }: { children: React.ReactNode }) => {
    const [keyHex, setKeyHex] = useState("");

    return (
        <KeyContext.Provider value={{ keyHex, setKeyHex }}>
            {children}
        </KeyContext.Provider>
    );
};
