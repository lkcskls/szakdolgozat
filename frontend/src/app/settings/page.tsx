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
import { changeAlgorithm, getAlgos, getUserEncDetails } from "@/lib/api"
import { useEffect, useState } from "react"
import { Spinner } from "@/components/Spinner"
import { useKey } from "@/components/KeyProvider"
import { GenSecretKey } from "@/components/GenSecretKey"
import KeyInpupt from "@/components/KeyInput"

export default function SettingsPage() {
    const [userAlgo, setUserAlgo] = useState<string>("");
    const [hasKey, setHasKey] = useState<boolean>(false);
    const [algos, setAlgos] = useState<{ name: string }[]>([]);
    const [selectedAlgo, setSelectedAlgo] = useState("");
    const [loading, setLoading] = useState<boolean>(true);
    const [updating, setUpdating] = useState<boolean>(false);
    const { keyHex } = useKey();

    //elérhető algoritmusok és a user adatainak lekérése betöltéskor
    useEffect(() => {
        const fetchAlgos = async () => {
            try {
                setLoading(true)
                const result = await getAlgos();
                setAlgos(result);
                const { algo, has_secret_key } = await getUserEncDetails();
                setUserAlgo(algo);
                setHasKey(has_secret_key);
            } catch (err) {
                console.log(err);
            } finally {
                setLoading(false)
            }
        };

        fetchAlgos();
    }, []);

    //algoritmusváltás
    async function handleSave() {
        setUpdating(true)
        try {
            await changeAlgorithm(selectedAlgo, keyHex)
            setUserAlgo(selectedAlgo)
        }
        catch (err) { console.log(err) }
        setUpdating(false)
    }

    //user adatok frissítése kulcsgenerálás dialog bezárása után
    async function handleKeyGeneration() {
        try {
            setLoading(true)
            const { algo, has_secret_key } = await getUserEncDetails();
            setUserAlgo(algo);
            setHasKey(has_secret_key);
        }
        catch (err) { console.log(err) }
        finally { setLoading(false) }
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
                                        {hasKey ? <>
                                            <div className="flex justify-between">
                                                <div>
                                                    <p><b>You have a secret key</b></p>
                                                </div>
                                                <div>
                                                    ✔️
                                                </div>
                                            </div>
                                        </> : <>
                                            <div className="flex justify-between">
                                                <div>
                                                    <p><b>You do not have a secret key</b></p>
                                                </div>
                                                <div>
                                                    ✖️
                                                </div>
                                            </div>
                                        </>}


                                        <br />

                                        {hasKey && keyHex == "" ? <>
                                            <p>To change algorithm enter your secret key</p>
                                            <KeyInpupt />
                                        </> :
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
                                                                <p><b>You already have a secret key</b></p>
                                                            </>
                                                            :
                                                            <>
                                                                <Label htmlFor="genKey">Generate your secret key:</Label>
                                                                <GenSecretKey onSuccess={handleKeyGeneration}></GenSecretKey>
                                                                <p><b>You can only generate a secret key once, so make sure not to lose it.</b></p>
                                                            </>
                                                        }
                                                        <p className="text-xs">Your files are all encrypted with one algorithm and one key. Changing either will cause every file to be re-encrypted.</p>

                                                    </div>
                                                </div>
                                            </form>
                                        }


                                    </>
                                }
                            </CardContent>
                            <CardFooter className="flex justify-between">
                                <Button disabled={updating || selectedAlgo == userAlgo} onClick={handleSave}>Save</Button>
                            </CardFooter>
                        </Card>
                    </div>
                </div>
            </SidebarInset>
        </SidebarProvider >
    )
}