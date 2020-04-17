class PeerStack {
    constructor() {
    }
    
    init() { 
        self = this;
        this.items = [];
        this.clients = [];
        this.peer = new Peer();
        this.peer.on('open', () => {$(self).trigger('open');});
        this.peer.on('connection', (conn) => {self.on_connect_from_client(conn);});
        this.peer.on('error', () => {console.log('error');});
        this.is_host = true;  
        this.is_connecting = false;        
        return this;
    }
        
    connect_to(host) {
        self = this;
        this.is_connecting = true;
        this.conn = this.peer.connect(host, {reliable:true});
        this.conn.on('open', () => {self.on_connect_to_host();});
        this.conn.on('error', () => {console.log('error');});
        
        // no idea why this fails to give either open or error sometimes, so try again
        setTimeout(() => {  if (self.is_connecting) self.connect_to(host);}, 2000);         
    }
    
    on_connect_to_host() {
        this.is_connecting = false;
        this.conn.on('data', (data) => {self.received_data(data, self.conn);});
        this.conn.send({type:"get-all"});
        this.is_host = false;
        this.items = [];
    }
    
    received_data(data, conn) {
        if (data.type == 'item') {
            if (this.is_host) {
                this.add(data.value);
            } else {
                this.items.push(data.value);
                $(this).trigger('added');
            }
        } else if (data.type == 'get-all') {
            conn.send({type:"all", value:this.items});
        } else if (data.type == 'all') {
            this.items = data.value;
            $(this).trigger('changed');
        }
    }
    
    on_connect_from_client(conn) {
        self = this;
        this.clients.push(conn);
        conn.on('data', (data) => {self.received_data(data, conn);});
    }
        
        

    add(item) {
        if (this.is_host) {
            for (var i in this.clients) {
                this.clients[i].send({type:"item", index:this.items.length, value:item});
            }
            this.items.push(item);
            $(this).trigger('added');
        } else {
            this.conn.send({type:"item", index:this.items.length, value:item});
        }
    }
    
    on(ev, func) {
        $(this).on(ev, func);
        return this;
    }
}

