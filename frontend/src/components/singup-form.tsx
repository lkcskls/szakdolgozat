"use client"

import { zodResolver } from "@hookform/resolvers/zod"
import { useForm } from "react-hook-form"
import { z } from "zod"
import { Button } from "@/components/ui/button"
import {
    Form,
    FormControl,
    FormDescription,
    FormField,
    FormItem,
    FormLabel,
    FormMessage,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { registerUser } from "@/lib/api"
import { useRouter } from "next/navigation"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card"

const formSchema = z.object({
    name: z.string().min(5, {
        message: "Name must be at least 5 characters.",
    }),
    email: z.string().email({
        message: "Invalid email format.",
    }),
    password: z.string().min(8, {
        message: "Password must be at least 8 characters.",
    }),
})

export function SignUpForm() {
    const router = useRouter();

    const form = useForm<z.infer<typeof formSchema>>({
        resolver: zodResolver(formSchema),
        defaultValues: {
            name: "",
            email: "",
            password: "",
        },
    })

    async function onSubmit(values: z.infer<typeof formSchema>) {
        try {
            const res = await registerUser(values.name, values.email, values.password);
            console.log("Siker:", res);

            router.push("/login");

        } catch (err: unknown) {
            if (err instanceof Error) {
                console.error("Hiba:", err.message)
            } else {
                console.error("Ismeretlen hiba:", err)
            }
        }
    }

    return (
        <div className={"flex flex-col gap-6"}>
            <Card>
                <CardHeader className="text-center">
                    <CardTitle className="text-xl">Welcome</CardTitle>
                    <CardDescription>
                        Create you account
                    </CardDescription>
                </CardHeader>
                <CardContent>

                    <Form {...form}>
                        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-8">

                            <FormField
                                control={form.control}
                                name="name"
                                render={({ field }) => (
                                    <FormItem>
                                        <FormLabel>Name</FormLabel>
                                        <FormControl>
                                            <Input placeholder="name" {...field} />
                                        </FormControl>
                                        <FormDescription>
                                            Your full name.
                                        </FormDescription>
                                        <FormMessage />
                                    </FormItem>
                                )}
                            />

                            <FormField
                                control={form.control}
                                name="email"
                                render={({ field }) => (
                                    <FormItem>
                                        <FormLabel>Email</FormLabel>
                                        <FormControl>
                                            <Input placeholder="email" {...field} />
                                        </FormControl>
                                        <FormDescription>
                                            Your main email address.
                                        </FormDescription>
                                        <FormMessage />
                                    </FormItem>
                                )}
                            />

                            <FormField
                                control={form.control}
                                name="password"
                                render={({ field }) => (
                                    <FormItem>
                                        <FormLabel>Password</FormLabel>
                                        <FormControl>
                                            <Input placeholder="password" type="password" {...field} />
                                        </FormControl>
                                        <FormDescription>
                                            Your secret password.
                                        </FormDescription>

                                        <FormMessage />
                                    </FormItem>
                                )}
                            />

                            <Button type="submit">Submit</Button>
                            <div className="text-center text-sm">
                                Have an account?{" "}
                                <a href="/login" className="underline underline-offset-4">
                                    Log in
                                </a>
                            </div>
                        </form>
                    </Form>
                </CardContent>
            </Card>
        </div>
    )
}
