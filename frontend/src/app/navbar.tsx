import Image from "next/image";

export default function NavBar(){
    return (
        <nav>
            <div className="flex px-8 py-2">
                <a href="/">
                    <Image src="/logo.png" alt="logo" width={400} height={400}></Image>
                </a>
            </div>
        </nav>
    )    
}