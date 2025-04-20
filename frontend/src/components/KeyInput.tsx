import { useState } from "react";
import { useKey } from "./KeyProvider";
import { Button } from "./ui/button";
import { Input } from "./ui/input";

export default function KeyInpupt() {
    const [input, setInput] = useState<string>("")
    const {keyHex, setKeyHex} = useKey();

    function handleKeyHexSave(){
        setKeyHex(input)
    }

    function handleKeyHexRemove(){
        setKeyHex("")
        setInput("")
    }

    return (
        <div className="flex gap-2">
            { keyHex === "" ? <>
                <Input type="text"value={ input } onChange={(e) => setInput(e.target.value)} placeholder="Type your secret key here..." className="w-128"/>
                <Button variant={"secondary"} onClick={handleKeyHexSave}>Save</Button>
            </> : <>
                <Button variant={"secondary"} onClick={handleKeyHexRemove}>Remove secret key</Button>
            </>}
        </div>
    )
}