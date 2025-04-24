"use client"

import { Button } from "@/components/ui/button"
import {
    Card,
    CardContent,
    CardDescription,
    CardFooter,
    CardHeader,
    CardTitle,
} from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
    Tabs,
    TabsContent,
    TabsList,
    TabsTrigger,
} from "@/components/ui/tabs"
import { SidebarInset, SidebarProvider, } from "@/components/ui/sidebar"
import { AppSidebar } from "@/components/app-sidebar"
import { SiteHeader } from "@/components/site-header"
import { useEffect, useState } from "react"
import { User, editUser, getUser } from "@/lib/api"



export default function TabsDemo() {
    const [user, setUser] = useState<User>({
        id: -1,
        name: "",
        email: "",
        algo: ""
    })
    const [newUser, setNewUser] = useState<User>({
        id: -1,
        name: "",
        email: "",
        algo: ""
    })
    const [loading, setLoading] = useState<boolean>(false)

    useEffect(() => {
        getUser().then(setUser);
    }, []);

    useEffect(() => {
        setNewUser(user)
    }, [user]);

    async function handleUpdateUser() {
        setLoading(true)
        try {
            await editUser(newUser)
            setUser(newUser)
        }
        catch { }
        finally {
            setLoading(false)
        }
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

                        <Tabs defaultValue="account" className="w-[400px]">
                            <TabsList className="grid w-full grid-cols-2">
                                <TabsTrigger value="account">Account</TabsTrigger>
                                <TabsTrigger value="password">Password</TabsTrigger>
                            </TabsList>
                            <TabsContent value="account">
                                <Card>
                                    <CardHeader>
                                        <CardTitle>Account</CardTitle>
                                        <CardDescription>
                                            Make changes to your account here. Click save when you are done.
                                        </CardDescription>
                                    </CardHeader>
                                    <CardContent className="space-y-2">
                                        <div className="mb-2">
                                            <b ><p>Your current profile info:</p></b>
                                        </div>
                                        <div className="flex justify-between">
                                            <div>
                                                <p><b>Name:</b></p>
                                            </div>
                                            <div>
                                                <p>{user.name}</p>
                                            </div>
                                        </div>
                                        <div className="flex justify-between">
                                            <div>
                                                <p><b>Email:</b></p>
                                            </div>
                                            <div>
                                                <p>{user.email}</p>
                                            </div>
                                        </div>

                                        <br />

                                        <div className="mb-2">
                                            <b ><p>You can make changes here:</p></b>
                                        </div>
                                        <div className="space-y-1">
                                            <Label htmlFor="name">New name</Label>
                                            <Input id="name" value={newUser.name} onChange={(e) =>
                                                setNewUser({ ...newUser, name: e.target.value })
                                            } />
                                        </div>

                                        <div className="space-y-1">
                                            <Label htmlFor="email">New email</Label>
                                            <Input id="email" value={newUser.email} onChange={(e) =>
                                                setNewUser({ ...newUser, email: e.target.value })
                                            } />
                                        </div>

                                    </CardContent>
                                    <CardFooter>
                                        <Button disabled={loading} onClick={handleUpdateUser}>Save changes</Button>
                                    </CardFooter>
                                </Card>
                            </TabsContent>
                            <TabsContent value="password">
                                <Card>
                                    <CardHeader>
                                        <CardTitle>Password</CardTitle>
                                        <CardDescription>
                                            Change your password here. After saving, you will be logged out.
                                        </CardDescription>
                                    </CardHeader>
                                    <CardContent className="space-y-2">
                                        <div className="space-y-1">
                                            <Label htmlFor="current">Current password</Label>
                                            <Input id="current" type="password" />
                                        </div>
                                        <div className="space-y-1">
                                            <Label htmlFor="new">New password</Label>
                                            <Input id="new" type="password" />
                                        </div>
                                    </CardContent>
                                    <CardFooter>
                                        <Button disabled={loading}>Save password</Button>
                                    </CardFooter>
                                </Card>
                            </TabsContent>
                        </Tabs>
                    </div>
                </div>
            </SidebarInset>
        </SidebarProvider>
    )
}
