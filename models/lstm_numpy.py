# models/lstm_numpy.py
import numpy as np
import joblib

class LSTMRegressor:
    def __init__(self, input_dim=11, hidden_dim=16, output_dim=1, lr=0.01, epochs=10, seq_len=5, batch_size=32):
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.output_dim = output_dim
        self.lr = lr
        self.epochs = epochs
        self.seq_len = seq_len
        self.batch_size = batch_size
        
        # Initialize weights (Xavier/Glorot Initialization)
        # Concatenated weights for gating: input, forget, cell, output
        # Shapes: W_x (4 * hidden, input), W_h (4 * hidden, hidden), b (4 * hidden, 1)
        limit_x = np.sqrt(6.0 / (input_dim + hidden_dim))
        limit_h = np.sqrt(6.0 / (hidden_dim + hidden_dim))
        
        self.W_x = np.random.uniform(-limit_x, limit_x, (4 * hidden_dim, input_dim))
        self.W_h = np.random.uniform(-limit_h, limit_h, (4 * hidden_dim, hidden_dim))
        self.b = np.zeros((4 * hidden_dim, 1))
        
        # Forget gate bias initialization to 1.0 (helps with learning long-term dependencies)
        self.b[hidden_dim:2*hidden_dim] = 1.0
        
        # Fully connected output layer
        limit_y = np.sqrt(6.0 / (hidden_dim + output_dim))
        self.W_y = np.random.uniform(-limit_y, limit_y, (output_dim, hidden_dim))
        self.b_y = np.zeros((output_dim, 1))

    def sigmoid(self, x):
        return 1.0 / (1.0 + np.exp(-np.clip(x, -500, 500)))

    def sigmoid_derivative(self, val):
        # val is already sigmoid(x)
        return val * (1.0 - val)

    def tanh_derivative(self, val):
        # val is already tanh(x)
        return 1.0 - val ** 2

    def create_sequences(self, X, y=None):
        """
        Converts X and y into sequences of shape (num_samples, seq_len, features)
        """
        X_seq, y_seq = [], []
        for i in range(len(X) - self.seq_len + 1):
            X_seq.append(X[i:i + self.seq_len])
            if y is not None:
                y_seq.append(y[i + self.seq_len - 1])
        
        X_seq = np.array(X_seq)
        if y is not None:
            y_seq = np.array(y_seq).reshape(-1, self.output_dim)
            return X_seq, y_seq
        return X_seq

    def forward(self, x_seq):
        """
        x_seq: sequence of inputs, shape (seq_len, input_dim)
        Returns:
            y: predicted output, shape (output_dim, 1)
            cache: dictionary of intermediate activations for backprop
        """
        T = x_seq.shape[0]
        H = self.hidden_dim
        
        h = {}
        c = {}
        f = {}
        i = {}
        tilde_c = {}
        o = {}
        gates = {}
        
        h[-1] = np.zeros((H, 1))
        c[-1] = np.zeros((H, 1))
        
        for t in range(T):
            xt = x_seq[t].reshape(-1, 1)
            
            # Linear combination
            gate_inputs = np.dot(self.W_x, xt) + np.dot(self.W_h, h[t-1]) + self.b
            gates[t] = gate_inputs
            
            # Split gate activations
            i[t] = self.sigmoid(gate_inputs[0:H])
            f[t] = self.sigmoid(gate_inputs[H:2*H])
            tilde_c[t] = np.tanh(gate_inputs[2*H:3*H])
            o[t] = self.sigmoid(gate_inputs[3*H:4*H])
            
            # Next cell state
            c[t] = f[t] * c[t-1] + i[t] * tilde_c[t]
            
            # Next hidden state
            h[t] = o[t] * np.tanh(c[t])
            
        # Linear output layer
        y = np.dot(self.W_y, h[T-1]) + self.b_y
        
        cache = {
            'x_seq': x_seq, 'h': h, 'c': c, 'f': f, 'i': i, 
            'tilde_c': tilde_c, 'o': o, 'gates': gates
        }
        return y, cache

    def backward(self, dy, cache):
        """
        dy: loss gradient w.r.t y, shape (output_dim, 1)
        """
        T = self.seq_len
        H = self.hidden_dim
        
        x_seq = cache['x_seq']
        h = cache['h']
        c = cache['c']
        f = cache['f']
        i = cache['i']
        tilde_c = cache['tilde_c']
        o = cache['o']
        gates = cache['gates']
        
        # Initialize gradients
        dW_x = np.zeros_like(self.W_x)
        dW_h = np.zeros_like(self.W_h)
        db = np.zeros_like(self.b)
        
        dW_y = np.dot(dy, h[T-1].T)
        db_y = dy.copy()
        
        dh = np.dot(self.W_y.T, dy)
        dc = np.zeros((H, 1))
        
        for t in reversed(range(T)):
            xt = x_seq[t].reshape(-1, 1)
            
            # Gradient of h[t]
            dh_t = dh
            
            # Gradient of output gate
            do_t = dh_t * np.tanh(c[t])
            dgate_o = do_t * self.sigmoid_derivative(o[t])
            
            # Gradient of cell state c[t]
            dc_t = dc + dh_t * o[t] * self.tanh_derivative(np.tanh(c[t]))
            
            # Gradient of candidate cell state tilde_c[t]
            dtilde_c_t = dc_t * i[t]
            dgate_tilde_c = dtilde_c_t * self.tanh_derivative(tilde_c[t])
            
            # Gradient of input gate i[t]
            di_t = dc_t * tilde_c[t]
            dgate_i = di_t * self.sigmoid_derivative(i[t])
            
            # Gradient of forget gate f[t]
            df_t = dc_t * c[t-1]
            dgate_f = df_t * self.sigmoid_derivative(f[t])
            
            # Concatenate gate gradients
            dgates = np.vstack((dgate_i, dgate_f, dgate_tilde_c, dgate_o))
            
            # Accumulate weight gradients
            dW_x += np.dot(dgates, xt.T)
            dW_h += np.dot(dgates, h[t-1].T)
            db += dgates
            
            # Compute gradients for previous step
            dh = np.dot(self.W_h.T, dgates)
            dc = f[t] * dc_t
            
        # Gradient clipping to prevent exploding gradients
        for grad in [dW_x, dW_h, db, dW_y, db_y]:
            np.clip(grad, -1.0, 1.0, out=grad)
            
        return dW_x, dW_h, db, dW_y, db_y

    def fit(self, X, y):
        # Format dataset to sequence matrix
        X_seq, y_seq = self.create_sequences(X, y)
        num_samples = X_seq.shape[0]
        
        # Adam Optimizer Variables
        m_Wx, v_Wx = np.zeros_like(self.W_x), np.zeros_like(self.W_x)
        m_Wh, v_Wh = np.zeros_like(self.W_h), np.zeros_like(self.W_h)
        m_b, v_b = np.zeros_like(self.b), np.zeros_like(self.b)
        m_Wy, v_Wy = np.zeros_like(self.W_y), np.zeros_like(self.W_y)
        m_by, v_by = np.zeros_like(self.b_y), np.zeros_like(self.b_y)
        
        beta1, beta2 = 0.9, 0.999
        eps = 1e-8
        t_step = 0
        
        for epoch in range(self.epochs):
            # Shuffle indices
            indices = np.arange(num_samples)
            np.random.shuffle(indices)
            
            epoch_loss = 0
            
            # Mini-batch loop
            for batch_start in range(0, num_samples, self.batch_size):
                batch_indices = indices[batch_start:batch_start + self.batch_size]
                
                # Gradients accumulator
                gW_x = np.zeros_like(self.W_x)
                gW_h = np.zeros_like(self.W_h)
                gb = np.zeros_like(self.b)
                gW_y = np.zeros_like(self.W_y)
                gby = np.zeros_like(self.b_y)
                
                batch_loss = 0
                
                for idx in batch_indices:
                    x_sample = X_seq[idx]
                    y_sample = y_seq[idx].reshape(-1, 1)
                    
                    # Forward
                    y_pred, cache = self.forward(x_sample)
                    
                    # Compute Loss (Mean Squared Error)
                    loss = 0.5 * np.sum((y_pred - y_sample) ** 2)
                    batch_loss += loss
                    
                    # Loss gradient
                    dy = y_pred - y_sample
                    
                    # Backward
                    dW_x, dW_h, db, dW_y, db_y = self.backward(dy, cache)
                    
                    gW_x += dW_x
                    gW_h += dW_h
                    gb += db
                    gW_y += dW_y
                    gby += db_y
                
                # Average gradients
                n_b = len(batch_indices)
                gW_x /= n_b
                gW_h /= n_b
                gb /= n_b
                gW_y /= n_b
                gby /= n_b
                
                epoch_loss += batch_loss / n_b
                
                # Update weights with Adam
                t_step += 1
                
                for param, grad, m, v in [
                    (self.W_x, gW_x, m_Wx, v_Wx),
                    (self.W_h, gW_h, m_Wh, v_Wh),
                    (self.b, gb, m_b, v_b),
                    (self.W_y, gW_y, m_Wy, v_Wy),
                    (self.b_y, gby, m_by, v_by)
                ]:
                    # Update biased first moment estimate
                    m *= beta1
                    m += (1 - beta1) * grad
                    
                    # Update biased second raw moment estimate
                    v *= beta2
                    v += (1 - beta2) * (grad ** 2)
                    
                    # Compute bias-corrected first moment estimate
                    m_hat = m / (1 - beta1 ** t_step)
                    # Compute bias-corrected second raw moment estimate
                    v_hat = v / (1 - beta2 ** t_step)
                    
                    # Update parameters
                    param -= self.lr * m_hat / (np.sqrt(v_hat) + eps)
            
    def predict(self, X):
        """
        Accepts X of shape (num_samples, features) and outputs predictions.
        To support standard Scikit-Learn API where prediction shape matches input shape,
        we pad predictions for the first (seq_len-1) samples with their immediate future predicted value.
        """
        X_seq = self.create_sequences(X)
        preds = []
        for x_sample in X_seq:
            y_pred, _ = self.forward(x_sample)
            preds.append(y_pred[0, 0])
        
        preds = np.array(preds)
        
        # Pad the first (seq_len - 1) samples with the first prediction to match X length
        padding = np.full(self.seq_len - 1, preds[0] if len(preds) > 0 else 0.0)
        return np.concatenate((padding, preds))

    def save(self, filepath):
        joblib.dump(self, filepath)

    @classmethod
    def load(cls, filepath):
        return joblib.load(filepath)
