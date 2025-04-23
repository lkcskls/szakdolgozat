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


export function GenSecretKey() {
    const { keyHex, setKeyHex } = useKey();

    return (
        <Dialog onOpenChange={async (open) => {
            if (open) {
                console.log("Dialog megnyílt!");
                const key = await genSecretKey(keyHex)
                setKeyHex(key);
            }
        }}>
            <DialogTrigger asChild>
                <Button variant="default">Generate</Button>
            </DialogTrigger>
            <DialogContent>
                <DialogHeader>
                    <DialogTitle>Here is your secret key</DialogTitle>
                    <DialogDescription>
                        To encrypt or decrypt any file, you will need this key, so handle it with care!
                        Encrypted files cannot be accessed without your secret key.
                        You can store your secret key in a text file or save it in a password manager.
                    </DialogDescription>
                </DialogHeader>

                <CopyableTextarea text={keyHex}></CopyableTextarea>

            </DialogContent>
        </Dialog>
    );
}
