const tempStore: string = "cbTemp";

const temp = {
    read: () => {
        return JSON.parse(localStorage.getItem(tempStore) || "{}");
    },
    write: (data: any) => {
        localStorage.setItem(tempStore, JSON.stringify(data));
    },
    remove: (key: string) => {
        let data = temp.read();
        delete data[key];
        temp.write(data);
    },

    set: (key: string, value: any, expire?: number) => {
        let data = temp.read();

        //make the expire a timestamp
        if (expire) { expire = Date.now() + expire; }
        else { expire = Date.now() + 1000 * 60 * 5; } //expire after 5 minutes 
        
        data[key] = {value: value, expire: expire};
        temp.write(data);
    },
    get: (key: string) => {
        let data = temp.read();

        if (!data[key]) { return null; }

        if (data[key].expire < Date.now()) {
            temp.remove(key);
            return null;
        }

        return data[key].value;
    },
    clear: () => {
        localStorage.removeItem(tempStore);
    }
}

export { temp };