import { NextRequest, NextResponse } from "next/server";

export async function middleware(req: NextRequest) {
    const sessionToken = req.cookies.get("session_token")?.value;

    if (!sessionToken) {
        return NextResponse.redirect(new URL("/login", req.url));
    }

    return NextResponse.next();
}

export const config = {
    matcher: [
        "/dashboard/:path*", 
        "/settings/:path*", 
        "/account/:path*"
    ]
};
