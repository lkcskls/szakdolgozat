"use client"

import { SidebarInset, SidebarProvider, } from "@/components/ui/sidebar"
import { AppSidebar } from "@/components/app-sidebar"
import { SiteHeader } from "@/components/site-header"
import {
    Card,
    CardContent,
    CardDescription,
    CardFooter,
    CardHeader,
    CardTitle,
} from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Button } from "@/components/ui/button"
import Link from "next/link"
import { changeAlgorithm, getAlgos, getUserAlgo } from "@/lib/api"
import { useEffect, useState } from "react"
import { Spinner } from "@/components/Spinner"
import { useKey } from "@/components/KeyProvider"

export default function SettingsPage() {
    const [userAlgo, setUserAlgo] = useState<string>("");
    const [hasKey, setHasKey] = useState<boolean>(false);
    const [algos, setAlgos] = useState<{ name: string }[]>([]);
    const [selectedAlgo, setSelectedAlgo] = useState("");
    const [loading, setLoading] = useState<boolean>(true);
    const {keyHex } = useKey();

    useEffect(() => {
        const fetchAlgos = async () => {
            try {
                setLoading(true)
                const result = await getAlgos();
                setAlgos(result);
                const { algo, hasSecretKey } = await getUserAlgo();
                setUserAlgo(algo);
                setHasKey(hasSecretKey);
            } catch (error) {
                console.error("Hiba az algoritmusok lekérésekor:", error);
            } finally {
                setLoading(false)
            }
        };

        fetchAlgos();
    }, []);

    function handleSave() {
        console.log(selectedAlgo)
        changeAlgorithm(selectedAlgo, keyHex)
        setUserAlgo(selectedAlgo)
    }

    return (
        <SidebarProvider
            style={
                {
                    "--sidebar-width": "calc(var(--spacing) * 72)",
                    "--header-height": "calc(var(--spacing) * 12)",
                } as React.CSSProperties
            }
        >
            <AppSidebar variant="inset" />

            <SidebarInset>
                <SiteHeader />

                <div className="flex flex-1 mt-15 justify-center p-4">
                    <div className="max-w-lg">

                        <Card className="w-[450px]">
                            <CardHeader>
                                <CardTitle><h1 className="text-2xl font-bold">Settings</h1></CardTitle>
                                <CardDescription></CardDescription>
                                <Link href="/account" className="underline text-black hover:opacity-50 transition">Your account setting are here</Link>
                            </CardHeader>
                            <CardContent>
                                {loading ?
                                    <Spinner />
                                    :
                                    <>
                                        <div className="flex justify-between">
                                            <div>
                                                <p><b>Your current algorithm for encryption:</b></p>
                                            </div>
                                            <div>
                                                <p>{userAlgo}</p>
                                            </div>
                                        </div>
                                        <div className="flex justify-between">
                                            <div>
                                            <p><b>You have a secret key:</b></p>
                                            </div>
                                            <div>
                                                <p>{hasKey ? <>Yes</> : <>No</>}</p>
                                            </div>
                                        </div>
                                        
                                        <br />

                                        <form>
                                            <div className="grid w-full items-center gap-4">
                                                <div className="flex flex-col space-y-1.5">
                                                    <Label htmlFor="algo">Change your algorithm:</Label>
                                                    <Select value={selectedAlgo} onValueChange={setSelectedAlgo}>
                                                        <SelectTrigger id="algo">
                                                            <SelectValue placeholder="Algorithms" />
                                                        </SelectTrigger>
                                                        <SelectContent position="popper">
                                                            {algos.map((algo) => (
                                                                <SelectItem key={algo.name} value={algo.name}>
                                                                    {algo.name}
                                                                </SelectItem>
                                                            ))}
                                                        </SelectContent>
                                                    </Select>

                                                    {hasKey ?
                                                        <>
                                                            <Label htmlFor="genKey">Generate </Label>
                                                            <Button>Generate</Button>
                                                        </>
                                                        :
                                                        <>
                                                            <Label htmlFor="genKey">Generate your secret key:</Label>
                                                            <Button>Generate</Button>
                                                        </>
                                                    }
                                                    <p className="text-xs">Select and save the chosen algoritm, than generate secret key!</p>
                                                    <p className="text-xs">All your files are encrypted with one algoritm and one key. If you change algorithm or generate new key, every encrypted file will be re-encrypted.</p>

                                                </div>
                                            </div>
                                        </form>
                                    </>
                                }
                            </CardContent>
                            <CardFooter className="flex justify-between">
                                <Button onClick={handleSave}>Save</Button>
                            </CardFooter>
                        </Card>
                    </div>
                </div>
            </SidebarInset>
        </SidebarProvider >
    )
}