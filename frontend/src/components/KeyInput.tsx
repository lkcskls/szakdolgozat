"use client"

import { useState } from "react";
import { useKey } from "./KeyProvider";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { verifySecretKey } from "@/lib/api";
import { toast } from "sonner";

export default function KeyInpupt() {
    const [input, setInput] = useState<string>("")
    const { keyHex, setKeyHex } = useKey();

    //kulcs mentése
    async function handleKeyHexSave() {
        try {
            const valid = await verifySecretKey(input)
            if (valid) {
                setKeyHex(input)
                toast("Secret key saved")
            }
            else toast("Invalid secret key")
        }
        catch (err) { console.log(err) }
    }

    //kulcs törlése
    function handleKeyHexRemove() {
        setKeyHex("")
        setInput("")
        toast("Secret key removed")
    }

    return (
        <div className="flex flex-wrap gap-2">
            {keyHex === "" ? <>
                <Input type="text" value={input} onChange={(e) => setInput(e.target.value)} placeholder="Type your secret key here..." className="min-w-0 flex-1 max-w-[600] w-full" style={{ minWidth: '350px' }} />
                <Button variant={"secondary"} onClick={handleKeyHexSave}>Save</Button>
            </> : <>
                <Button variant={"secondary"} onClick={handleKeyHexRemove}>Remove secret key</Button>
            </>}
        </div>
    )
}