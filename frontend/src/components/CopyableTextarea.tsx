"use client";

import * as React from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Copy } from "lucide-react";
import { toast } from "sonner";

type CopyableTextareaProps = {
    text: string;
};

export function CopyableTextarea({ text }: CopyableTextareaProps) {

    const handleCopy = () => {
        navigator.clipboard.writeText(text)
            .then(() => toast.success("Copied"))
            .catch(() => toast.error("Copy failed"));
    };

    return (
        <div className="space-y-4">
            <Textarea
                value={text}
                readOnly
                className="w-full resize-y text-sm break-all"
                rows={4}
            />
            <Button onClick={handleCopy} variant="secondary">
                <Copy className="mr-2 h-4 w-4" />
                Copy
            </Button>
        </div>
    );
}
