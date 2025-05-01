"use client";

import * as React from "react";
import { Button } from "@/components/ui/button";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
    DialogTrigger
} from "@/components/ui/dialog";
import { CopyableTextarea } from "./CopyableTextarea";
import { useKey } from "./KeyProvider";
import { genSecretKey } from "@/lib/api";

type GenSecretKeyProps = {
    onSuccess: () => Promise<void>;
};

export function GenSecretKey({ onSuccess }: GenSecretKeyProps) {
    const { keyHex, setKeyHex } = useKey();

    return (
        <Dialog onOpenChange={async (open) => {
            //titkos kulcs generálás
            if (open) {
                try {
                    const key = await genSecretKey(keyHex);
                    setKeyHex(key);
                } catch (err) {
                    console.error(err);
                }
            }
            //fallback függvény, felhasználói adatok frissítése
            else{
                onSuccess();
            }
        }}>
            <DialogTrigger asChild>
                <Button variant="default">Generate</Button>
            </DialogTrigger>
            <DialogContent>
                <DialogHeader>
                    <DialogTitle>Here is your secret key</DialogTitle>
                    <DialogDescription>
                        To encrypt or decrypt your files, you will need this key, so make sure to handle it carefully! <br />
                    </DialogDescription>
                </DialogHeader>

                <CopyableTextarea text={keyHex}></CopyableTextarea>

            </DialogContent>
        </Dialog>
    );
}
