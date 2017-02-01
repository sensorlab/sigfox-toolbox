module.exports = function(RED) {
	function sigfoxDeviceFilterNode(config) {
		RED.nodes.createNode(this, config);
		this.device = config.device;
		var node = this;
		
		this.on('input', function(msg) {
			if(!node.device) {
				node.warn("sigfox device filter: Device not set");
				return;
			}

			var message;
			try {
				if(typeof msg.payload === 'string' || msg.payload instanceof String)
                    message = JSON.parse(msg.payload);
                else
                    message = msg.payload;
			}
			catch(err) {
				node.warn("sigfox device filter: Can't parse received message");
				return;
			}
			if(!message instanceof Object || message == null) {
				node.warn("sigfox device filter: Message is not an object");
				return;
			}
			if(!message.hasOwnProperty("device")) {
				node.warn("sigfox device filter: Missing property 'device'");
				return;
			}


			if(String(message.device).toLowerCase() == node.device.toLowerCase()) {
				node.send(msg);
			}
		});
	}
	RED.nodes.registerType("sigfox device filter", sigfoxDeviceFilterNode);
}
