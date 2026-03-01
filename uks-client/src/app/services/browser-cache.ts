import { Injectable } from "@angular/core";

@Injectable({
  providedIn: 'root',
})
export class BrowserCache {
    private role: string = '';
    private user: any = null;

    getRole() {
        return this.role;
    }

    getUser() {
        return this.user;
    }

    setRole(item: string) {
        this.role = item;
    }

    setUser(item: any) {
        this.user = item;
    }

    clearAll() {
        this.role = '';
        this.user = null;
    }
}
