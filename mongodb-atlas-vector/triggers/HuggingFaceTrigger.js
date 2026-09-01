exports = async function(changeEvent) {
    // Get the full document from the change event.
    const doc = changeEvent.fullDocument;
    // Define the Hugging Face API url and key.
    const url = 'https://api-inference.huggingface.co/models/intfloat/multilingual-e5-large';
    // Use the name you gave the value of your API key in the "Values" utility inside of App Services
    const hf_key = context.values.get("HUGGINGFACE_VALUE");
    try {
        console.log(`Processing document with id: ${doc._id}`);

        // Call HugginFace API to get the embeddings.
        let response = await context.http.post({
            url: url,
            headers: {
                'Authorization': [`Bearer ${hf_key}`],
                'Content-Type': ['application/json'],
                'x-wait-for-model': ['true']
            },
            //body: JSON.stringify({ inputs: doc.log_message }),
            body: JSON.stringify(doc.log_message),
            encodeBodyAsJSON: true
        });

        // Parse the JSON response
        let responseData = EJSON.parse(response.body.text());
        console.log(`Response: ${JSON.stringify(responseData)}`);

        // Check the response status.
        if(response.statusCode === 200) {
           console.log("Successfully received embedding.");

           const embedding = responseData;
           //const embedding = responseData[0].embedding;
           console.log(embedding.length);

            // Use the name of your MongoDB Atlas Cluster
            const collection = context.services.get("Cluster0").db("RealTimeRAG").collection("RealTimeRAG");

            // Update the document in MongoDB.
            const result = await collection.updateOne(
                { _id: doc._id },
                // The name of the new field you'd like to contain your embeddings.
                { $set: { log_message_embedding: embedding }}
            );

            if(result.modifiedCount === 1) {
                console.log("Successfully updated the document.");
            } else {
                console.log("Failed to update the document.");
            }
        } else {
            console.log(`Failed to receive embedding. Status code: ${response.statusCode}`);
        }

    } catch(err) {
        console.error(err);
    }
};
