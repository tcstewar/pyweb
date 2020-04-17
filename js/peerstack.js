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
        console.log('connect_to: '+host);
        console.log(this);
        this.conn = this.peer.connect(host, {reliable:true});
        this.conn.on('open', () => {self.on_connect_to_host();});
        this.conn.on('error', () => {console.log('error');});
        setTimeout(() => {  if (self.is_connecting) self.connect_to(host);}, 2000);
                 
    }
    
    on_connect_to_host() {
        this.is_connecting = false;
        console.log('on_connect_to_host');
        console.log(this);
        this.conn.on('data', (data) => {self.received_data(data);});
        this.is_host = false;
        this.items = [];
    }
    
    received_data(data) {
        console.log('received: '+data);
        if (this.is_host) {
            this.add(data);
        } else {
            this.items.push(data);
            $(this).trigger('added');
        }
    }
    
    on_connect_from_client(conn) {
        self = this;
        console.log(this);
        this.clients.push(conn);
        conn.on('data', (data) => {self.received_data(data);});
        for (var i in this.items) {
            console.log('send: '+this.items[i]);
            conn.send(this.items[i]);
        }
    }
        
        

    add(item) {
        if (this.is_host) {
            this.items.push(item);
            $(this).trigger('added');
            for (var i in this.clients) {
                console.log('send: '+item);
                this.clients[i].send(item);
            }
        } else {
            this.conn.send(item);
        }
    }
    
    on(ev, func) {
        $(this).on(ev, func);
        return this;
    }
}

